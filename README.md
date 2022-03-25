# ft_looker_deploy_git_action

## Set up
* This is based on the workflow defined [here](https://github.com/sam-pitcher/multi_instance_demo) to configure:
  * Ensure your Looker environment is correctly configured based on the above instructions:
    * Create API users on both production and development environments. We need to ensure these users have permission to see LookML dashboards and to write to the target folder
    * Set up the git connection for the two Looker instances as follows:
      * Development should take place on the development instance and changes should be deployed to the default 'master' branch
      * 'Advanced Deploy Mode' should be used in the production instance and a specific branch should be chosen to use as production. Make note of this name
    * Ensure the 'LookML Dashboard Organization' Labs feature is enabled in dev + prod - this will allow us move LookML dashboards into different folders.
  * Copy the code in this `.github` folder into your LookML project
  * Set the Looker API credentials (id, secret and URL) for both dev + prod environments as secrets in the github repository:
    * The development secrets should be saved with the names `LOOKER_CLIENT_ID_1`, `LOOKER_CLIENT_SECRET_1`, `LOOKER_BASE_URL_1`
    * The production secrets should be saved with the names `LOOKER_CLIENT_ID_2`, `LOOKER_CLIENT_SECRET_2`, `LOOKER_BASE_URL_2`
  * **Ensure you read through the 'Configuration' section below to correctly use this tool**

## What this does
* This compares the current state of instance 1 against instance 2
  * Fetches all of the LookML dashboards defined in both instances and the folders they live in
    * *NOTE - this will only look at those dashboards visible to the API-calling user, so Admin API credentials are preferable, and this will not see LookML dashboard files that have not been included in any model file*
  * Compare the two instances to find:
    * (a) dashboards that are net new, i.e. dashboards that exist in instance 1 and not in instance 2 (as identified by their id, i.e. `model_name::dashboard_name`)
    * (b) dashboards that exist in both instances, but do not reside in the target folder
      * *NOTE - There is a command line flag regarding what to do with these (see below)*
  * Dashboards that have been deleted should be handled automatically by Looker and do not need treatment here

## Configuration
* The `looker_deploy.yml` file dictates how Github executes this script.
* By default, this is triggered when a pull request is merged into a branch named `prod`. This can be changed by editing lines 3-5 in the yaml file
  * A reference can be [found here](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow)
* When a PR is merged into the `prod` branch, the `looker_deploy.py` script will be executed
* This script uses command line arguments which can be edited in the yaml file. Please change the following:
  * `--project_id` or `-p`, Name of the Production Looker Project **Required**
  * `--release_branch` or `-b`, Identifier for the git ref or branch to deploy to production mode on the production Looker instance **Required**
  * `--lookml_folder` or `-f`, ID of the target destination folder for LookML dashboards **Required**
  * `--handle_moved_dashboards` or `-m` A flag - if you include this **all** LookML dashboards not in the target folder in the production instance will be moved there. If ommitted, only net new LookML dashboards will be moved to this folder.
* These arguments do not need to be configured as they read the github secrets we defined earlier: 
  * `--looker_sdk_1`: Credentials for SDK1 (id, secret, url in that order)
  * `--looker_sdk_2`: Credentials for SDK2 (id, secret, url in that order)
