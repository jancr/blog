pyenv install 3.7.5
pyenv virtualenv blog
pip install -r requirements.txt
sudo cp blog.service /etc/systemd/system/blog.service

# setup nginx
sudo cp nginx_config/blog /etc/nginx/sites-available/blog
sudo ln -s /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/



