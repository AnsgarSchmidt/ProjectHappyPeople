# ProjectHappyPeople

```
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get dist-upgrade -y
sudo apt-get install -y vim mc git screen python-pip python-virtualenv 
sudo apt-get install -y build-essential git cmake pkg-config
sudo apt-get install -y libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install -y libxvidcore-dev libx264-dev
sudo apt-get install -y libgtk2.0-dev
sudo apt-get install -y libatlas-base-dev gfortran
sudo apt-get install -y python2.7-dev python3-dev

git clone https://github.com/AnsgarSchmidt/ProjectHappyPeople.git
cd ProjectHappyPeople
virtualenv .
. bin/activate
pip install -r requirements.txt
```

Install OpenCV3
http://www.pyimagesearch.com/2015/10/26/how-to-install-opencv-3-on-raspbian-jessie/
```
cd ~
wget -O opencv.tgz https://github.com/opencv/opencv/archive/3.2.0.tar.gz
tar xvzf opencv.zip
cd opencv-3.2.0/
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D INSTALL_PYTHON_EXAMPLES=ON \
      -D BUILD_EXAMPLES=ON ..
make -j4
sudo make install
sudo ldconfig
cd /home/pi/ProjectHappyPeople/lib/python2.7
ln -s /usr/local/lib/python2.7/site-packages/cv2.so .
```