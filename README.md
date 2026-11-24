## Arcadyan Speed Home WiFi

The Arcadyan Speed Home WiFi is an access point bundled with Arcadyan Speedport Smart 3.

## Obtaining Root Shell

1. Remove the plastic shell
2. Solder your UART leads based on the diagram, don't connect VCC
<img width="960" height="1280" alt="uart" src="https://github.com/user-attachments/assets/96c2a08c-d255-4c33-8e25-d725f959331e" style="width:300px;" />

4. Connect UART to your adapter (could be a Pi, FTDI or something else) with baud rate 115200 and the AP via Ethernet and boot it
5. While it boots spam the space key to interrupt the boot process
6. When you reach the `topaz>` prompt use `printenv` to print the enviroment variables, the following ones are the ones we care about
```
ipaddr=192.168.1.200
serverip=192.168.1.11
loadaddr=0x83000000
```
6. `ipaddr` is the AP's address while `serverip` is our PC. Use `setenv` like the example bellow to set them correctly
```
setenv ipaddr 192.168.1.99
setenv serverip 192.168.1.254
setenv netmask 255.255.255.0 
```
7. Set up a TFTP server on your PC with the patched image and download it on the AP's RAM using
```
tftpboot 0x83000000 patched.bin
```
8. Boot the patched image using `bootm 0x83000000`
9. Once the boot process finishes press enter at the prompt, you should be dropped at the shell
10. Use `passwd root` to change the password and then `pcb_cli 'DeviceManagement.SSH.[AccessType=lan].Enable=1'` to enable `dropbear`
11. Confirm you can access the AP over SSH using 
```
ssh -o HostKeyAlgorithms=+ssh-rsa -o MACs=+hmac-sha1 root@192.168.1.99 
```

## Explanation
Since we can interrupt U-Boot the first thing I tried was adding `init=/bin/rc` but the image is configured with `CONFIG_CMDLINE_FORCE` so it had no effect. 
<br>The next strategy was to dump the image, patch it and boot it from RAM.
<br>It's pretty easy to dump the very small filesystem using either `md` on UBoot or by dumping the through hole NOR chip using something like a CH431A.
<br>Once we do we can extract the image with ease, I have attached my own dump in this repo.
<br>From `printenv` we see that
```
mtdparts=spi_flash:256k(uboot),64k(uboot_env),64k(uboot_env_bak),14336k(linux_safety),14336k(linux_live),3584k(data), -(data_pkey)
```
So the first image is at offset 256+64+64=384k=393216 bytes so `0x60000`, immediately followed by the other image which is byte identical (Greek units never received firmware upgrades).
The prefix is `0x2000` so `binwalk` finds the first image at `0x62000`
```
401408                             0x62000                            LZMA compressed data, properties: 0x5D,
                                                                      dictionary size: 33554432 bytes, compressed
                                                                      size: 10481842 bytes, uncompressed size:
                                                                      37771504 bytes
15081472                           0xE62000                           LZMA compressed data, properties: 0x5D,
                                                                      dictionary size: 33554432 bytes, compressed
                                                                      size: 10481842 bytes, uncompressed size:
                                                                      37771504 bytes
```
We can add `0x2000` to the compressed size to find `0xA010B2` which is the true size of the image and then carve it one byte at a time using
```
dd if=Speedport_Smart_Repeater-SPI_DUMP.bin of=image.bin bs=1 skip=$((0x60000)) count=$((0xa010b2))
``` 
After carving the first bank's image I tried patching it to with `init=/bin/sh` and it worked but Arcadyan's `/bin/login` binary was still running instead.
<br>By Googling the prompt (`Please press Enter to activate this console.`) I was able to find about busybox's `askfirst` which was pointing to /bin/login and sure enough after patching it, I had a shell.
<br>Using the `patcher.py` script on the 10 MiB image, you can recreate the modified image yourself.

