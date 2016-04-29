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
GUEST= "dev%d" % randint(1000, 3000)
VROOTDISKSIZE="10G"
VCPUS=2
VMEM=2048
NETWORK="bridge=virbr1,model=virtio"

# guest image format
FORMAT="qcow2"
POOL="vm"
POOL_PATH="/home/vm"

def system(cmd):
    """
    Runs a shell command, and returns the output, err, returncode
    :param cmd: The command to run.
    :return:  Tuple with (output, err, returncode).
    """
    ret = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    out, err = ret.communicate()
    returncode = ret.returncode
    return out, err, returncode

def get_meta_data():
    meta_data = ("instance-id: iid-{0}\n"
                 "hostname: {0}\n"
                 "local-hostname: {0}").format(GUEST)
    return meta_data

def get_user_data():
    user_data = ("#cloud-config\n"
                 "hostname: %s"
                 "password: passw0rd\n"
                 "chpasswd: { expire: False }\n"
                 "ssh_pwauth: True\n",
                 "package_upgrade: false") % GUEST
    return user_data

def create_pool():
    if system("virsh pool-list|grep %s -c" % POOL)[2]:
        return system(("virsh pool-define-as --name {0} --type dir --target {1} && "
                       "virsh pool-autostart {0} && "
                       "virsh pool-build {0} &&"
                       "virsh pool-start {0}").format(POOL, POOL_PATH))[1:]
    return('', 0)

def create_cloud_init_iso():
    with open('user_data','w') as fh:
        fh.write(get_user_data())
    with open('meta_data','w') as fh:
        fh.write(get_meta_data())
    return system(("genisoimage -output configuration.iso "
        "-volid cidata -joliet -rock user_data meta_data"))[1:]


def copy_cloud_init_iso():
    if not create_cloud_init_iso()[1]:
        err, returncode = system("mv configuration.iso %s/%s.configuration.iso" % (POOL_PATH, GUEST))[1:]
        if err:
            return (err, returncode)
        return system("virsh pool-refresh %s" % POOL)[1:]
    return ('cloud init iso not created\n', 1)


def copy_image_to_libvirt_pool(image_name):
    if not os.path.isfile("%s/%s" % (POOL_PATH,image_name)):
        copy(image_name, POOL_PATH)
        system("virsh pool-refresh %s" % POOL)

def clone_cloud_image(image_name):
    copy_image_to_libvirt_pool(image_name)
    return system(("virsh vol-clone --pool {0} {1} {2}.root.img && "
                   "virsh vol-resize --pool {0} {2}.root.img {3}").format(POOL, image_name,
                                                                 GUEST, VROOTDISKSIZE))[1:]

def create_vm():
    return system(("virt-install "
                  "--name {0} "
                  "--ram {1} "
                  "--vcpus={2} "
                  "--memballoon virtio "
                  "--network {3} "
                  "--boot hd "
                  "--disk vol={4}/{0}.root.img,format={5},bus=virtio "
                  "--disk vol={4}/{0}.configuration.iso,bus=virtio "
                  "--noautoconsole").format(GUEST, VMEM, VCPUS, NETWORK, POOL, FORMAT))[1:]

if __name__ == "__main__":
    parser = ArgumentParser(prog='vmcreation', description='Create virtual machine using KVM')
    parser.add_argument("image", help="downloaded qcow2 image name")
    args = parser.parse_args()
    if os.getuid():
        print "Execution Permission Denied (use sudo)"
        sys.exit(1)
    err, returncode = create_pool()
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
    err, returncode = copy_cloud_init_iso()
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
    err, returncode = clone_cloud_image(args.image)
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
    err, returncode = create_vm()
    if returncode:
        sys.stderr.write(err)
        sys.exit(1)
