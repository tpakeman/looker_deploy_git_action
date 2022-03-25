from typing import Dict, Tuple
import looker_sdk, logging, argparse, os
from datetime import datetime
from looker_sdk.sdk.api40.methods import Looker40SDK
from looker_sdk.sdk.api40.models import WriteUserAttributeWithValue
from looker_sdk.rtl import api_settings
from looker_sdk.error import SDKError

DEBUG = True

# Set up Logging
logger = logging.getLogger('Github Looker Auto Deploy')
logger.setLevel(logging.DEBUG)

log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh = logging.FileHandler('looker_deploy.log')
fh.setFormatter(log_format)
logger.addHandler(fh)

if DEBUG:
    log_format_simple = logging.Formatter("%(levelname)s - %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(log_format_simple)
    logger.addHandler(sh)

class CustomSDKSettings(api_settings.ApiSettings):
    """Custom Looker API settings to allow us to initialise with multiple SDK credentials"""
    def __init__(self, *args, **kw_args):
        try:
            self.custom_credentials = kw_args.pop("credentials")
        except KeyError:
            self.sdk_num = None
        super().__init__(*args, **kw_args)

    def read_config(self):
        config = super().read_config()
        if self.custom_credentials is not None:
            config["client_id"], config["client_secret"], config["base_url"] = self.custom_credentials
        return config


def init_sdks(args: argparse.Namespace) -> Tuple[Looker40SDK, Looker40SDK]:
    """Set up SDKs"""
    dev_sdk = init_sdk(args.looker_sdk_1)
    prod_sdk = init_sdk(args.looker_sdk_2)
    if DEBUG:
        assert(test_envs(dev_sdk, prod_sdk))
    return dev_sdk, prod_sdk


def smoke_test_api(client: Looker40SDK) -> None:
    """Test the API is working by setting a user attribute"""
    uas = client.all_user_attributes()
    me = client.me().id
    target = [u for u in uas if u.name == 'api_test'][0].id
    value = WriteUserAttributeWithValue(value=f'Attribute updated at {datetime.now()}')
    client.set_user_attribute_user_value(me, target, value)


def test_envs(client1: Looker40SDK, client2: Looker40SDK) -> bool:
    """Test the API is working by setting a user attribute for both instances"""
    try:
        smoke_test_api(client1)
        smoke_test_api(client2)
        return True
    except SDKError as _e:
        return False


def init_sdk(credentials: list):
    try:
        sdk = looker_sdk.init40(config_settings=CustomSDKSettings(credentials=credentials))
        logger.info(f"Successfully authed into Looker SDK with base_url {credentials[2]}")
        return sdk
    except Exception as e:
        logger.error(f"Failed to log in to Looker SDK:{e}")


def deploy_ref(client: Looker40SDK, args: argparse.Namespace) -> None:
    """Attempt to deploy a Looker ref to production for a specific project"""
    try:
        client.deploy_ref_to_production(project_id=args.project_id, branch=args.release_branch)
        logger.info(f'Production mode for {args.project_id} updated to use ref "{args.release_branch}"')
    except Exception as e:
        logger.error(f'Failed to Update Production mode for {args.project_id}:\n{e}')


def is_lookml(dashboard):
    """Check if a dashoard is a LookML dashboard"""
    return dashboard.model is not None and '::' in dashboard.id


def diff_lookml_dashboards(client1: Looker40SDK, client2: Looker40SDK, args: argparse.Namespace) -> Dict:
    """Compare LookML dashboards and their folder locations for both instances
        Return a dict with net new dashboards, and dashboards that are not in the target folder.
        Updates and deletions should be handled automatically by Looker
    """
    try:
        from_dash = {d.id: d.folder.id for d in client1.all_dashboards() if is_lookml(d)}
        logger.info(f'Found {len(from_dash)} LookML dashboards in instance 1')
        to_dash = {d.id: d.folder.id for d in client2.all_dashboards() if is_lookml(d)}
        logger.info(f'Found {len(to_dash)} LookML dashboards in instance 2')
    except Exception as e:
        logger.error(f'Failed to fetch LookML dashboards:\n{e}')
    results = {"new": [], "not_in_target": [] }
    to_dash_ids = to_dash.keys()
    for key in from_dash.keys():
        if key not in to_dash_ids:
            results["new"].append(key)
        else:
            if to_dash[key] != args.lookml_folder:
                results['not_in_target'].append((key, to_dash[key])) # Tuple of dash id and folder id
    return results


def update_lookml_dashboards(diff: Dict, client: Looker40SDK, args: argparse.Namespace):
    """Move the dashboards"""
    moved = 0
    for d in diff['new']:
        try:
            client.move_dashboard(d, args.lookml_folder)
            moved += 1
            logger.info(f'Successfully moved new LookML dashboard {d} into folder {args.lookml_folder}')
        except Exception as e:
            logger.error(f'Failed to move new LookML dashboard {d} into folder {args.lookml_folder}')
    if args.handle_moved_dashboards:
        for d in diff['not_in_target']:
            try:
                client.move_dashboard(d[0], args.lookml_folder)
                moved += 1
                logger.info(f'Successfully moved existing LookML dashboard {d[0]} from folder {d[1]} into folder {args.lookml_folder}')
            except Exception as e:
                logger.info(f'Failed to move existing LookML dashboard {d[0]} from folder {d[1]} into folder {args.lookml_folder}')
    if moved == 0:
        logger.info("Did not move any dashboards")
    else:
        logger.info(f"Successfully moved {moved} dashboards")


def configure_cli():
    """Set up a simple CLI to receive inputs"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id', '-p', help='Name of the Looker Project', required=True)
    parser.add_argument('--release_branch', '-b', help='Identifier for the git ref to deploy', required=True)
    parser.add_argument('--lookml_folder', '-f', help='Target destination folder for LookML dashboards', required=True)
    parser.add_argument('--looker_sdk_1', nargs=3, help='Credentials for SDK1 (id, secret, url in that order)', required=True)
    parser.add_argument('--looker_sdk_2', nargs=3, help='Credentials for SDK2 (id, secret, url in that order)', required=True)
    parser.add_argument('--handle_moved_dashboards', '-m', action='store_true', help='Include to move all LookML dashboards to target folder')
    return parser.parse_args()


def main():
    """Glue it all together"""
    args = configure_cli()
    dev_sdk, prod_sdk = init_sdks(args)
    diff = diff_lookml_dashboards(dev_sdk, prod_sdk, args)
    deploy_ref(prod_sdk, args)
    update_lookml_dashboards(diff, prod_sdk, args)


if __name__ == '__main__':
    main()
