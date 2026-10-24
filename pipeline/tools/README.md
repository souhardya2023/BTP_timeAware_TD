# tools

`export_project_details.py` - one-time script that built `project_dataset` (pairs, `properties_all_pairs.csv`, `project_details/`) and `project_with_bugs_dataset` from the working folders of the study (needs those folders, so it cannot be run from `final_folder` alone). Kept as documentation of where the data came from.

`export_sonarqube_server.py` - exports the SonarQube server (http://localhost:9000) into `project_dataset/sonarqube_server`; reads the token from `SONAR_TOKEN`, writes nothing secret.
