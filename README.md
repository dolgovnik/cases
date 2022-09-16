# Cases DataBase
This is database of Care cases with fulltext search.  
Actual data is not included it this repository.

## Technical details
Data is stored in **PostgreSQL**. Database is initialized on startup phase via `init/init.sql` sctipt. This script creates tables and fills it with data from `init/csv_data/*.csv` files. This csv's files is not included to repository.  
Fulltext search index is maid through several fields: **support_ticket_number**, **subject**, **description**, **technical_analysis**, **temporary_solution**, **solution_details**, **recovery_actions**, **summary_of_analysis**, **root_cause_description**. 

Service logic is realized with help of **Flask** framework. **Flask** keeps connection pool to **PostgreSQL** database. **Flask** is deployed in **Docker** with `tiangolo/uwsgi-nginx-flask:python3.8-alpine-2021-10-26` image. Users sessions are stored in **Redis**. Session validation made with help of decorator function.  

Client side is made with **HTML** and **JS**. **HandsOnTable** javascript library is used to show search results in web browser.  

All three services (**Flask**, **Redis**, **PostgreSQL**) are orchestrated with docker-compose.
