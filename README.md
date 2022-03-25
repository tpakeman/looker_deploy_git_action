# ft_looker_deploy_git_action
*due March 18th*

## Set up
* Follow instructions [here](https://github.com/sam-pitcher/multi_instance_demo) to configure:
  * Looker environments and branch configuration
    * Ensure the API user has permissions to see LookML dashboards and to write to the target folder
    * Ensure the 'LookML Dashboard Organization' Labs feature is enabled in Prod - this will move LookML dashboards rather than copy them.
  * Github secrets
    * *NOTE - here we need to set up two sets of secrets.*
      * The development secrets should be saved as `LOOKER_CLIENT_ID_1`, `LOOKER_CLIENT_SECRET_1`, `LOOKER_BASE_URL_1`
      * The production secrets should be saved as `LOOKER_CLIENT_ID_2`, `LOOKER_CLIENT_SECRET_2`, `LOOKER_BASE_URL_2`

## What this does
* This compares the current state of instance 1 against instance 2
  * Fetches all of the LookML dashboards defined in both instances and the folders they live in
    * *NOTE - this will only look at those dashboards visible to the API-calling user, so Admin credentials should be used*
    * *NOTE - this will not see LookML dashboards that exist in the LookML model but have not been included in a model file*
  * Compare all lookml dashboards on instances 1 + 2 to find:
    * dashboards that are net new, i.e. dashboard exists in dev instance and does not exist in prod instance
    * dashboards that already exist in production, but are not in the target folder
      * There is a command line flag regarding what to do with these (see below)
    * dashboards that have been deleted will be handled automatically by Looker

## Configuration
* This is run by github. Change the `looker_deploy.yml` file to configure the following command line arguments:
  * `--project_id` or `-p`, Name of the Looker Project **Required**
  * `--release_branch` or `-b`, Identifier for the git ref or branch to deploy **Required**
  * `--lookml_folder` or `-f`, ID of the target destination folder for LookML dashboards **Required**
  * `--handle_moved_dashboards` or `-m` If you include this, any LookML dashboards not in the target folder will be moved there. If not, only new LookML dashboards will be moved there.
* These arguments do not need to be configured as they read the github secrets we defined earlier: 
  * `--looker_sdk_1`: Credentials for SDK1 (id, secret, url in that order)
  * `--looker_sdk_2`: Credentials for SDK2 (id, secret, url in that order)
