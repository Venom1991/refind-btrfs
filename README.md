# refind-btrfs

### Table of Contents
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Example](#example)
  - [Implementation](#implementation)
  - [Further Efforts](#further-efforts)

## Description
This tool is used to automate a few tedious tasks required to boot into [Btrfs](https://en.wikipedia.org/wiki/Btrfs) snapshots from [rEFInd](https://en.wikipedia.org/wiki/REFInd). It is to rEFInd what [grub-btrfs](https://github.com/Antynea/grub-btrfs) is to [GRUB](https://en.wikipedia.org/wiki/GNU_GRUB).

What it does is the following:
* Gathers information about block devices present in the system
* Identifies the [ESP](https://en.wikipedia.org/wiki/EFI_system_partition) (either by GPT GUID or MBR ID)
* Gathers information about mounted filesystems (from [mtab](https://en.wikipedia.org/wiki/Mtab)) which are present on all of the found block devices
* Identifies the root mount point and gathers information about the subvolume which is mounted at said mount point
* Searches for snapshots of the identified subvolume in the configured directory (or directories)
* Searches for rEFInd's main config file on the ESP and parses it to extract [manual boot stanzas](https://www.rodsbooks.com/refind/configfile.html#stanzas) from it (included configs are also analyzed, if present)
* Selects the configured number of latest snapshots and uses them as such if they are writable and if any aren't, it either (depending on the configuration):
  * sets their read-only flag to false, thus making them writable
  * creates new writable snapshots from them in the configured location
* Aligns the root mount point in the [fstab](https://en.wikipedia.org/wiki/Fstab) file of each selected snapshot with the snapshot itself
* Deletes outdated previously created writable snapshots (if any exist)
* Generates new manual boot stanzas from identified ones where every relevant field is aligned with each selected snapshot
* Finally, it saves the generated manual boot stanzas in separate config files (outputs them to a subdirectory) and includes each file in the main config file so as not to needlessly clutter it

In case a separate /boot partition is detected only the fields relevant to / are modified ("subvol" and/or "subvolid") while the "loader" and "initrd" fields (the former may also be nested within the "options" field) remain unaffected.  
It goes without saying that the consequence of having this kind of a setup is being unable to mitigate a problematic kernel upgrade by simply booting into a snapshot.

This tool will also detect a situation where / is mounted as a snapshot (which means that you've already booted into one), issue a warning and simply exit whereas, for instance, [Snapper](http://snapper.io/) will happily continue creating its snapshots, regardless. This behavior is configurable and enabled by default.

## Prerequisites
The following conditions (some are probably superfluous at this point) must be satisfied in order for this tool to function correctly:
* mounted ESP (no automatic discovery and/or mounting is supported)
* Btrfs formatted filesystem with a subvolume mounted as /
* at least one snapshot of the root subvolume
* rEFInd installation present on the ESP
* at least one manual boot stanza (found in rEFInd's main config file or in any of the additional config files included within it) defined such that (see the [ArchWiki](https://wiki.archlinux.org/index.php/REFInd#Manual_boot_stanza) for an example) its own "options" field or any such field belonging to at least one of its sub-menus contains definitions of the following boot loader options:
  * the "root" option must be matched with the root partition (by PARTUUID or PARTLABEL), its filesystem (by UUID or LABEL) or with a block device (by name) which itself represents the root partition
  * the "rootflags" option must define a "subvol" suboption which is matched with the root subvolume's logical path and/or a "subvolid" suboption which is matched with the root subvolume's ID

## Installation
This tool is currently available only in the [AUR](https://aur.archlinux.org/packages/refind-btrfs/) which means that [Arch Linux](https://www.archlinux.org/) users (as well as users of derivative distributions, I imagine) can easily install it.

It comes with a script (refind-btrfs) which can be used to perform the described steps, on-demand (root privileges are required to run it). There is also a [systemd](https://en.wikipedia.org/wiki/Systemd) service aptly named **refind-btrfs.service** which runs the tool in a background mode of operation where the described steps are performed automatically once a change (snapshot creation or deletion) happens in the watched snapshot directories which are the same ones as those in which it searches for snapshots. If you are using Snapper along with its capability to take regular snapshots on boot this service should take these into account as well because it is set to start before Snapper's relevant service does so (the one named snapper-boot.service).  
Before running the script for the first time or enabling and starting the service make sure to at least check and perhaps modify the config file (/etc/refind-btrfs.conf) to suit your own needs.

If you wish to check the current status and log output of the running service you can do so by executing:
```
systemctl status refind-btrfs
journalctl -u refind-btrfs -b
```

Alternatively, there exists a PyPI [package](https://pypi.org/project/refind-btrfs/) but bear in mind that since [libbtrfsutil](https://github.com/kdave/btrfs-progs/tree/master/libbtrfsutil) isn't available on PyPI it needs to be already present in the system site packages (its Python bindings, to be precise) because it cannot be automatically pulled in as a dependency. Chances are that it is available for your distribution of choice (search for a package named "btrfs-progs") but you most probably already have it installed as I suppose you are using Btrfs, after all.  
Also, every file contained in [this](https://github.com/Venom1991/refind-btrfs/tree/master/src/refind_btrfs/data) directory should be copied to the following locations:
* refind-btrfs script to /usr/bin (or wherever it is you keep your system-wide executables)
* refind-btrfs.conf-sample as refind-btrfs.conf (without the "-sample" suffix) to /etc
* refind-btrfs.service to /usr/lib/systemd/system (if you are using systemd and wish to utilize the snapshot directory watching feature)

You should also create an empty directory named refind-btrfs in /var/lib as the tool expects that it is present.

## Configuration
Every option is thoroughly explained in the sample config [file](https://github.com/Venom1991/refind-btrfs/blob/master/src/refind_btrfs/data/refind-btrfs.conf-sample).  
In case you've opted to use the provided systemd service and wish to change the search directories (in this context, these are actually watched directories) in the config file while it is running you must restart it manually after doing so because the directory observer is started only once and an automatic restart is not performed.

The default configuration is meant to enable seamless integration with Snapper simply because I'm using it but the tool itself doesn't depend on it and ought to function with different setups. Also, by default the tool is configured for creating new writable snapshots intended for booting instead of in-place modification of the found snapshots' read-only flags as I believe this is the safer (or perhaps even saner) choice.

It is imperative that you don't just blindly try to boot into a given snapshot (simply because no errors were reported) before verifying the generated manual boot stanza, either by inspecting the file contents in which it was saved or by viewing the boot loader [options](https://www.rodsbooks.com/refind/using.html#boot_options) using rEFInd and also not before verifying the chosen snapshot's fstab file.

## Example
Given a setup such as this one:
* device /dev/nvme0n1 where:
  * the ESP is on /dev/nvme0n1p3 mounted at /efi
  * / is on /dev/nvme0n1p8
  * /boot is included in /dev/nvme0n1p8 (**not** a separate partition)
* the subvolume mounted as / is named @
* fstab file's root mount point:
```
UUID=95250e8a-5870-45df-a7b3-3b3ee8873c16 / btrfs rw,noatime,compress-force=zstd:2,ssd,space_cache=v2,commit=15,subvolid=256,subvol=/@ 0 0
```
* manual boot stanza defined in the refind.conf file (rEFInd's main config file, in this case):  
```
menuentry "Arch Linux - Stable" {
    icon /EFI/refind/icons/os_arch.png
    volume ARCH
    loader /@/boot/vmlinuz-linux
    initrd /@/boot/initramfs-linux.img
    options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@ initrd=@\boot\intel-ucode.img"
    submenuentry "Boot - fallback" {
        initrd /@/boot/initramfs-linux-fallback.img
    }
    submenuentry "Boot - terminal" {
        add_options "systemd.unit=multi-user.target"
    }
}
```
* five read-only snapshots located in the /.snapshots directory where this directory is itself mounted as a subvolume named @snapper-root (this last bit isn't particularly relevant):

    | Absolute Path          | Time of Creation    | Subvolume ID |
    | ---------------------- | ------------------- | ------------ |
    | /.snapshots/1/snapshot | 10-12-2020 01:00:00 | 498          |
    | /.snapshots/2/snapshot | 11-12-2020 02:00:00 | 499          |
    | /.snapshots/3/snapshot | 12-12-2020 03:00:00 | 500          |
    | /.snapshots/4/snapshot | 13-12-2020 04:00:00 | 501          |
    | /.snapshots/5/snapshot | 14-12-2020 05:00:00 | 502          |

* refind-btrfs.conf file changed such that the "selection_count" option is set to 3 instead of the default 5

When run, this tool should select the latest three snapshots (3, 4 and 5 from the list) and create new, writable ones from these in the directory configured by the "destination_dir" option where each snapshot is named by formatting the time of creation ("YYYY-mm-dd_HH-MM-SS") of the snapshot it was created from, adding a "rwsnap" prefix to it and also adding the original snapshot's subvolume ID as a suffix. In the rare case when different snapshots have identical timestamps their monotonic numerical IDs are there to ensure uniqueness.

Afterwards, the resultant snapshots' generated names should look like this:
* rwsnap_2020-12-12_03-00-00_ID500,
* rwsnap_2020-12-13_04-00-00_ID501 and
* rwsnap_2020-12-14_05-00-00_ID502

This naming scheme makes sense to me because when choosing a snapshot to boot from you most probably want to know when the original snapshot was created and not the one created from it because the time delay depends on when this tool was run and, if sufficiently large, can completely mislead you. If you've chosen to use the systemd service this delay shouldn't be significant (measuring a mere few seconds at worst, ideally).  

The most recent snapshot's fstab file should (after being modified) contain a root mount point which looks like this:  

```
UUID=95250e8a-5870-45df-a7b3-3b3ee8873c16 / btrfs rw,noatime,compress-force=zstd:2,ssd,space_cache=v2,commit=15,subvolid=503,subvol=/@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502 0 0
```
I'm assuming here that the next available subvolume ID was 503 (an increment of one) which implies that the writable snapshot was created immediately after the original snapshot was taken but that doesn't necessarily have to be the case and its specific value doesn't ultimately matter that much as long as it directly corresponds to the newly created snapshot which it absolutely should (otherwise, mounting it as / would fail due to the mismatch).

With this setup the newly created snapshot ended up being nested under the root subvolume but you can of course make your own adjustments as you see fit. This tool will only create the destination directory in case it doesn't exist. It won't do anything other than that.  
I've personally created another subvolume named @rw-snapshots directly under the default filesystem subvolume (ID 5) and mounted it at /root/.refind-btrfs. In my case the logical path of rwsnap_2020-12-14_05-00-00_ID502 would be /@rw-snapshots/rwsnap_2020-12-14_05-00-00_ID502.

A generated manual boot stanza's file name is formatted like "{volume}_{loader}.conf" and converted to all lowercase letters which would result in, for this example, a file named "arch_vmlinuz-linux.conf". This file is then saved in a subdirectory (relative to rEFInd's root directory) named "btrfs-snapshot-stanzas" and finally included in the main config file by appending an "include" directive which would, again for this example, look like this: "include btrfs-snapshot-stanzas/arch_vmlinuz-linux.conf". This last step is performed only once, during an initial run. Afterwards, it is detected as already being included in the main config file.

You are free to rearrange the appended include directives however you want, this tool does not care about where exactly they appear in the main config file. This is particularly useful in case you've defined multiple boot stanzas (each one pointing to a different kernel image, for example) and wish to alter the order of the boot menu entries.

The generated file's contents (representing the generated stanza) should look like this:
```
menuentry "Arch Linux - Stable (rwsnap_2020-12-14_05-00-00_ID502)" {
    icon /EFI/refind/icons/os_arch.png
    volume ARCH
    loader /@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502/boot/vmlinuz-linux
    initrd /@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502/boot/initramfs-linux.img
    options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502 initrd=@\root\.refind-btrfs\rwsnap_2020-12-14_05-00-00_ID502\boot\intel-ucode.img"
    submenuentry "Arch Linux - Stable (rwsnap_2020-12-13_04-00-00_ID501)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/initramfs-linux.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501 initrd=@\root\.refind-btrfs\rwsnap_2020-12-13_04-00-00_ID501\boot\intel-ucode.img"
    }
    submenuentry "Arch Linux - Stable (rwsnap_2020-12-12_03-00-00_ID500)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/initramfs-linux.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500 initrd=@\root\.refind-btrfs\rwsnap_2020-12-12_03-00-00_ID500\boot\intel-ucode.img"
    }
}
```
As you've probably noticed, this tool leverages rEFInd's overriding features, that is to say "submenuentry" sections are used to incorporate successive snapshots into the stanza itself by overriding the "loader", "initrd" and "options" fields of the main boot stanza which itself represents the latest snapshot.

If you've configured this tool to also take into account the original boot stanza's sub-menus the resultant generated boot stanza should look like this:
```
menuentry "Arch Linux - Stable (rwsnap_2020-12-14_05-00-00_ID502)" {
    icon /EFI/refind/icons/os_arch.png
    volume ARCH
    loader /@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502/boot/vmlinuz-linux
    initrd /@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502/boot/initramfs-linux.img
    options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502 initrd=@\root\.refind-btrfs\rwsnap_2020-12-14_05-00-00_ID502\boot\intel-ucode.img"
    submenuentry "Boot - fallback (rwsnap_2020-12-14_05-00-00_ID502)" {
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-14_05-00-00_ID502/boot/initramfs-linux-fallback.img
    }
    submenuentry "Boot - terminal (rwsnap_2020-12-14_05-00-00_ID502)" {
        add_options "systemd.unit=multi-user.target"
    }
    submenuentry "Arch Linux - Stable (rwsnap_2020-12-13_04-00-00_ID501)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/initramfs-linux.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501 initrd=@\root\.refind-btrfs\rwsnap_2020-12-13_04-00-00_ID501\boot\intel-ucode.img"
    }
    submenuentry "Boot - fallback (rwsnap_2020-12-13_04-00-00_ID501)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/initramfs-linux-fallback.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501 initrd=@\root\.refind-btrfs\rwsnap_2020-12-13_04-00-00_ID01\boot\intel-ucode.img"
    }
    submenuentry "Boot - terminal (rwsnap_2020-12-13_04-00-00_ID501)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501/boot/initramfs-linux.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-13_04-00-00_ID501 initrd=@\root\.refind-btrfs\rwsnap_2020-12-13_04-00-00_ID501\boot\intel-ucode.img systemd.unit=multi-user.target"
    }
    submenuentry "Arch Linux - Stable (rwsnap_2020-12-12_03-00-00_ID500)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/initramfs-linux.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500 initrd=@\root\.refind-btrfs\rwsnap_2020-12-12_03-00-00_ID500\boot\intel-ucode.img"
    }
    submenuentry "Boot - fallback (rwsnap_2020-12-12_03-00-00_ID500)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/initramfs-linux-fallback.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500 initrd=@\root\.refind-btrfs\rwsnap_2020-12-12_03-00-00_ID500\boot\intel-ucode.img"
    }
    submenuentry "Boot - terminal (rwsnap_2020-12-12_03-00-00_ID500)" {
        loader /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/vmlinuz-linux
        initrd /@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500/boot/initramfs-linux.img
        options "root=PARTUUID=048d6fcd-c88c-504d-bd51-dfc0a5bf762d rw add_efi_memmap rootflags=subvol=@/root/.refind-btrfs/rwsnap_2020-12-12_03-00-00_ID500 initrd=@\root\.refind-btrfs\rwsnap_2020-12-12_03-00-00_ID500\boot\intel-ucode.img systemd.unit=multi-user.target"
    }
}
```

A couple of notable details are the fact that the "add_options" field (if it exists) of any given sub-menu belonging to a successive snapshot is merged with the "options" field of the corresponding snapshot's sub-menu and also the fact that the latest snapshot's sub-menus implicitly inherit those main stanza's fields which they themselves do not override in the original boot stanza. Consequently, these sub-menus' definitions are intentionally similar to those of their counterparts found in the original boot stanza.

## Implementation
Most relevant dependencies:
* block device and ESP information is gathered using [lsblk](https://man7.org/linux/man-pages/man8/lsblk.8.html) (supports JSON output)
* mtab information is gathered using [findmnt](https://man7.org/linux/man-pages/man8/findmnt.8.html) (same remark applies regarding the output)
* all of the mentioned subvolume and snapshot operations are performed using [libbtrfsutil](https://github.com/kdave/btrfs-progs/tree/master/libbtrfsutil)
* [ANLTR4](https://github.com/antlr/antlr4) was used to generate the lexer and parser required for rEFInd config files' analyses
* [Watchdog](https://github.com/gorakhargosh/watchdog) is used for the snapshot directory watching feature and is utilized in a non-recursive fashion (watches all of the configured search directories as well as directories nested under these, up to configured maximum depth reduced by one)
* [python-systemd](https://github.com/systemd/python-systemd) is used for notifying systemd about the service's readiness (because its type is set to "notify") and also for logging to the journal

[Shelve](https://docs.python.org/3/library/shelve.html) is used to keep track of the currently processed snapshots and also to avoid analyzing the rEFInd config file each time as it is quite an expensive task. A new analysis is performed in case the current and actual times of modification differ ([st_mtime](https://docs.python.org/3/library/os.html#os.stat_result.st_mtime) is used for that purpose) which means that simply touching the file should also trigger a new analysis (file hashes aren't computed nor consequently compared). This fact also explains the need for a directory in /var/lib as the database file resides in it.

The directory watching mechanism is a bit unfortunate in a sense that it is way overkill for the task at hand. Even though Watchdog is a great, battle-tested library and many people use it, I feel that this solution isn't particularly well suited to this tool but it will simply have to suffice for now as I don't have a better idea (grub-btrfs also relies on a similar mechanism), at least not until the Btrfs authors develop [this](https://btrfs.wiki.kernel.org/index.php/Project_ideas#Send_notifications_about_important_events) useful feature or something akin to it.

## Further Efforts
Currently, this tool won't clean up after itself in case, for instance, creating writable snapshots succeeds but generating a manual boot stanza from them fails (for whatever reason). The correct thing to do would be to delete these snapshots altogether (thus undoing the changes made by the previous step or roll-backing as it is often called) meaning that the whole run is considered to be successful if and only if all of the steps it performed were successful.  
This behavior would then be comparable with the [atomicity](https://en.wikipedia.org/wiki/Atomicity_(database_systems)) principle to which most database systems adhere. The previously mentioned scenario is covered in a different way by issuing a relevant warning on the next attempt to run the tool (because the writable snapshots already exist at this point in time and they aren't expected to) but also continuing to perform successive steps. This isn't a general solution, of course, but more of a workaround for this one possible scenario.  
With that said, being somehow able to preview changes proposed by this tool would also be beneficial, especially after altering its configuration.

A more elaborate snapshot selection mechanism would be appreciated, comparable to what Snapper does, that is selecting a configurable number of daily, weekly, etc. snapshots to be included in the generated manual boot stanza.

Generated boot stanzas use the same OS icon as the original boot stanza but a custom icon would help to visually differentiate these stanzas. Somehow incorporating the Btrfs logo into the currently used OS icon would perhaps suffice, either by generating a new icon on-demand or by creating and packaging a complete icon set ahead of time. It would also be useful if the formatting of the strings used to identify bootable snapshots was configurable, that is the format string itself.

But, before trying to implement any of these shiny features this project's source code should be properly documented and tests should be written for it because, presently, there aren't any. The latter is also a pretty considerable effort due to the sheer number of different test cases. Luckily, all of the external dependencies (OS commands, third-party library calls and similar) are abstracted away which means that no significant preparatory steps regarding the codebase to be tested are required beforehand.
