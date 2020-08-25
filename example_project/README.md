# Example project for Django bot engine

This project helpful you run simple example of chatbot on django-bot-engine.
This project deploying on docker containers and have two image, where one
 is postgres database and second is web application on Django framework.

## Installing 

Clone the repository, go to the project directory and run docker containers:
```bash
git clone https://terentjew-alexey/django-bot-engine/releases/master.zip
cd django-bot-engine/example_project
sudo docker-compose up -d
```

Migrate a tables, create your superuser account and collect static files.
```bash
sudo docker-compose exec app python manage.py migrate
sudo docker-compose exec app python manage.py createsuperuser
sudo docker-compose exec app python manage.py collectstatic
```

Enter to example.com/admin/ site.

Change the site domain in the section Site > Sites to your domain.
If you dont have registered domain name, you must make Let's Encrypt certificate on ...

You must have a registered bot account and its authentication token.

Log in and go to Django Bot Engine > Messengers > Add


