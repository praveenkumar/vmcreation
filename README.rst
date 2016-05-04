This script is used to create vm (using libvirt) from cloud images.

Pre-requirements
----------------

Packages:-

- libvirt
- virt-install
- genisoimage
- qemu-img


For Fedora

::

 dnf install -y libvirt virt-install genisoimage qemu-img

For CentOS/RHEL
 
::

 yum install -y libvirt virt-install genisoimage qemu-img


How to use
----------

Step-1: Download cloud images in same directory.

- Fedora: https://getfedora.org/en/cloud/download/ (qcow2 Image)
- CentOS: http://cloud.centos.org/centos/7/images/ (qcow2 Image)
- Ubuntu: https://cloud-images.ubuntu.com/releases/16.04/release/ (img files)

Step-2: Start vmcreation script

::

 sudo python vmcreation.py <downloaded_image_name>

Step-3: Connect to console

::
 
 sudo virsh console <vm_name>
