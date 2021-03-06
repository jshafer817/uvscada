from uvscada import gxs700
from uvscada import gxs700_util
from uvscada import util

import argparse
import glob
import os
import usb1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--bin', '-b', action='store_true', help='Store .bin in addition to .png')
    parser.add_argument('--hist-eq', '-e', action='store_true', help='Equalize histogram')
    parser.add_argument('--dir', default='out', help='Output dir')
    parser.add_argument('--force', '-f', action='store_true', help='Force trigger')
    parser.add_argument('--number', '-n', type=int, default=1, help='number to take')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = gxs700_util.open_dev(usbcontext)
    gxs = gxs700.GXS700(usbcontext, dev, verbose=args.verbose)
    
    fn = ''
    
    if not os.path.exists(args.dir):
        os.mkdir(args.dir)
    
    taken = 0
    imagen = 0
    while glob.glob('%s/capture_%03d*' % (args.dir, imagen)):
        imagen += 1
    print 'Taking first image to %s' % ('%s/capture_%03d.bin' % (args.dir, imagen),)
    
    def scan_cb(itr):
        if args.force and itr == 0:
            print 'Forcing trigger'
            gxs.sw_trig()
        
    def cb(imgb):
        global taken
        global imagen
        
        if args.bin:
            fn = os.path.join(args.dir, 'capture_%03d.bin' % imagen)
            print 'Writing %s' % fn
            open(fn, 'w').write(imgb)

        def save(fn, eq):
            print 'Decoding %s' % fn
            if eq:
                buff = gxs700_util.histeq(imgb)
            else:
                buff = imgb
            img = gxs700.GXS700.decode(buff)
            print 'Writing %s' % fn
            img.save(fn)
        
        save(os.path.join(args.dir, 'capture_%03d.png' % imagen), eq=False)
        if args.hist_eq:
            save(os.path.join(args.dir, 'capture_%03de.png' % imagen), eq=True)

        taken += 1
        imagen += 1
    
    gxs.cap_binv(args.number, cb, scan_cb=scan_cb)


