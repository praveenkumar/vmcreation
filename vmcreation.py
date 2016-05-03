#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2016  Praveen Kumar <kumarpraveen.nitdgp@gmail.com>
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# vmcreation - Create VM using cloud qcow2 images (fedora, centos)


"""
Reference:
 - https://github.com/clauded/virt-tools/blob/master/virt-install-cloud.sh
 - https://github.com/kushaldas/tunir


Sample Usage:
    $ python vmcreation.py f24
    $ python vmcreattion.py centos7
"""

import os
import sys
import subprocess
from argparse import ArgumentParser
from shutil import copy
from random import randint

# Specify vm preferences for your guest
NAME= "dev%d" % randint(1000, 3000)
VROOTDISKSIZE="10G"
VCPUS=1
VMEM=1024
BRIDGE="virbr1"
NETWORK="bridge=virbr1,model=virtio"

# guest image format
POOL_PATH="/home/vm"

def system(cmd):
    """
    Runs a shell command, and returns the output, err, returncode
    :param cmd: The command to run.
    :return:  Tuple with (output, err, returncode).
    """
    print cmd
    ret = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    out, err = ret.communicate()
    returncode = ret.returncode
    return out, err, returncode

def get_meta_data():
    meta_data = ("instance-id: id-{0}\n"
                 "local-hostname: {0}\n").format(NAME)
    return meta_data

def get_user_data():
    user_data = ("#cloud-config\n"
                 "password: passw0rd\n"
                 "chpasswd: { expire: False }\n"
                 "ssh_pwauth: True\n")
    return user_data

def create_cloud_init_iso():
    with open('user-data','w') as fh:
        fh.write(get_user_data())
    with open('meta-data','w') as fh:
        fh.write(get_meta_data())
    return system(("genisoimage -output %s/%s.configuration.iso "
        "-volid cidata -joliet -rock user-data meta-data") % (POOL_PATH, NAME))[1:]

def copy_image_to_libvirt_pool(image_name):
    if not os.path.isfile("%s/%s" % (POOL_PATH,image_name)):
        copy(image_name, POOL_PATH)

def create_qemu_image(image_name):
    copy_image_to_libvirt_pool(image_name)
    return system(("qemu-img create -f qcow2 -b {0} {1}/{2}.root.img {3}").format(image_name, POOL_PATH,
                                                                              NAME, VROOTDISKSIZE))[1:]

def create_vm():
    return system(("virt-install --import "
                  "--name {0} "
                  "--ram {1} "
                  "--vcpus={2} "
                  "--network bridge={3},model=virtio "
                  "--disk path={4}/{0}.root.img "
                  "--disk path={4}/{0}.configuration.iso "
                  "--accelerate "
                  "--force "
                  "--graphics none").format(NAME, VMEM, VCPUS, BRIDGE, POOL_PATH))[1:]

if __name__ == "__main__":
    parser = ArgumentParser(prog='vmcreation', description='Create virtual machine using KVM')
    parser.add_argument("image", help="downloaded qcow2 image name")
    args = parser.parse_args()
    if os.getuid():
        print "Execution Permision Denied (use sudo)"
        sys.exit(1)
    err, returncode = create_cloud_init_iso()
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
    err, returncode = create_qemu_image(args.image)
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
    err, returncode = create_vm()
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
