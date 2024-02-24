#!/usr/bin/env bash
#
# Bash QEMU image file utilities module
#
# qemu-mount, qemu-umount, qemu-trim, qemu-compress - image file utilities
#
# Copyright GPL v2: 2023-2024 By Dr Colin Kong
#


set -u

hostname=$(uname -n)
username=$(id -un)
mount_user=${SUDO_USER:-$username}
drive_tmpdir="/tmp/qemu-${mount_user%:*}"


#
# Function to parse options
#
options() {
    help() {
        echo "Usage: $0 <options>"
        echo
        echo "qemu-mount    - Mount QEMU drive image partitions"
        echo "qemu-umount   - Unmount QEMU drive image partitions"
        echo "qemu-trim     - Trim QEMU drive image partitions"
        echo "qemu-compress - Compress QEMU drive image"
        echo
        echo "Options:"
        echo "  -h, --help  Show this help message and exit"
        echo "  -a          Select all mounted drive image file."
        echo "  <device>    Select drive image file (ie file.qcow2)."
        exit $1
    }

    drives=
    case "${0##*/}" in
    *-mount*)
        mode=mount
        ;;
    *-umount*)
        all=
        mode=unmount
        ;;
    *-trim*)
        mode=trim
        ;;
    *-compress*)
        mode=compress
        ;;
    *)
        help 0
        ;;
    esac
    while getopts "ah" option
    do
        case $option in
        a)
            local process_list=$(ps -ef)
            drives=$(echo "$process_list" | grep "qemu-nbd --connect /dev/nbd" | sed -e "s@.*/dev/nbd[^ ]* @@;s/ --.*//")
            ;;
        h)
            help 0
            ;;
        *)
            help 1
            ;;
        esac
    done
    shift $((OPTIND - 1))
    case ${1:-} in
    --help)
      help 0
      ;;
    --*)
      help 1
      ;;
    esac
    drives="$drives $*"
}


#
# Function to become root user
#
become_root() {
    [ "$username" = root ] && return
    echo -e "\033[33mSwitch root@$hostname: sudo \"$0\"\033[0m"
    exec sudo "$0" $args_list
}


#
# Function to create QEMU drive snapshot image
#
snapshot_drive() {
    [ -f "$2" ] && return
    echo -e "\nqemu-img create -F qcow2 -b $(realpath $1) -f qcow2 $2"
    qemu-img create -F qcow2 -b $(realpath $1) -f qcow2 $2
}


#
# Function to mount QEMU drive image partitions
#
mount_image() {
    image="$1"
    if [ "$(echo "$image" | grep base)" ]  # Drive base image files uses snapshots
    then
        mkdir -p $drive_tmpdir && chmod go= $drive_tmpdir
        snapshot_drive $image $drive_tmpdir/$image
        chown -R ${mount_user}:$(id -g $mount_user) $drive_tmpdir
        image="$drive_tmpdir/$image"
    fi

    become_root
    modprobe nbd max_part=8
    local device=$(lsblk -list -o NAME,SIZE | awk '/nbd.* 0B$/ {print $1; exit}')
    [ ! "$device" ] && echo "Unable to find unused \"/dev/nbd*\" device" && exit 1

    echo -e "\nqemu-nbd --connect /dev/$device \"$image\" --discard=unmap --detect-zeroes=unmap"
    qemu-nbd --connect /dev/$device "$(realpath "$image")"  --discard=unmap --detect-zeroes=unmap
    sleep 0.25
    for part in $(lsblk -list -o NAME | grep "^${device}p" | sed -e "s/${device}p//")
    do
        local mount="/mnt/qemu${device#nbd}p$part"
        mkdir -p $mount
        if [ "$(lsblk -list -o "NAME,FSTYPE" | grep -E "${device}p$part  *(vfat|ntfs)")" ]
        then
            echo "mount -o uid=$mount_user,gid=$(id -gn $mount_user),umask=022,fmask=133 /dev/${device}p$part $mount"
            mount -o uid=$mount_user,gid=$(id -gn $mount_user),umask=022,fmask=133 /dev/${device}p$part $mount
        else
            echo "mount /dev/${device}p$part $mount"
            mount /dev/${device}p$part $mount
        fi
    done
}


#
# Function to unmount QEMU drive image partitions
#
unmount_image() {
    local process_list=$(ps -ef)
    device=$(echo "$process_list" | grep "qemu-nbd .*/dev/nbd.* $(realpath "${1#$hostname:}") " | sed -e "s@.*/dev/@/dev/@;s/ .*//")
    [ "$device" ] || return

    become_root
    modprobe nbd max_part=8
    echo
    for mount in $(df 2> /dev/null | grep "^${device}p" | awk '{print $NF}')
    do
        echo "umount $mount"
        umount $mount || return
    done
    qemu-nbd --disconnect $device
}


#
# Function to trim QEMU drive image partitions
#
trim_image() {
    case ${1##*/} in
    *base*)
        ;;
    *)
        mount_image "$1"
        UNIT=$?
        echo -e "\nfstrim -av"
        fstrim -av | grep "/qemu${UNIT}p" | sort -k5
        unmount_image "$1"
        ;;
    esac
}


#
# Function to compress QEMU drive image
#
compress_image() {
   case "$1" in
    *.qcow2)
        echo "qemu-img convert -f qcow2 \"$1\" -O qcow2 -c -o compression_type=zstd \"$1.part\""
        qemu-img convert -f qcow2 "$1" -O qcow2 -c -o compression_type=zstd "$1.part"
        [ $? = 0 ] || continue
        echo "mv \"$1\" \"$1.orig\""
        mv "$1" "$1.orig" || continue
        echo "mv \"$1.part\" \"$1\""
        mv "$1.part" "$1"
        ;;
    esac
}


#
# Function to show mounted QEMU drive image partitions
#
mount_info() {
   local devices=$(lsblk -o "NAME,SIZE" 2> /dev/null | awk '/^nbd.* [1-9]/ {print $1}')
   local process_list=$(ps -ef)
   echo
   for device in $devices
   do
       echo "$process_list" | grep "qemu-nbd .*$device .*qcow2" | sed -e "s/[.]qcow2 .*/.qcow2/;s/.* /$hostname:/"
       lsblk --noheadings -o "NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT" /dev/$device
   done
}


options "$@"

args_list="$@"
for drive in $drives
do
    ${mode}_image $drive
done
mount_info
