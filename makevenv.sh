pyenv install 3.7.5
mkvirtualenv blog
workon blog
pip install -r requirements.txt
cp blog.service /etc/systemd/system/blog.service

# setup nginx
cp nginx_config/blog /etc/nginx/sites-available/blog
ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/



