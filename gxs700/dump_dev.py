from uvscada import gxs700_util
from uvscada import util

import argparse
import binascii
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump device data')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    util.add_bool_arg(parser, '--eeprom', default=False, help='Dump only EEPROM')
    util.add_bool_arg(parser, '--flash', default=False, help='Dump only flash')
    util.add_bool_arg(parser, '--hexdump', default=False, help='Instead of writing out, just hexdump')
    parser.add_argument('dout', nargs='?', default='dump', help='File out')
    args = parser.parse_args()

    usbcontext, dev, gxs = gxs700_util.ez_open_ex()
    
    if not args.hexdump:
        if not os.path.exists(args.dout):
            os.mkdir(args.dout)
        _t = util.IOLog(out_fn=os.path.join(args.dout, 'out.txt'))

    alll = not (args.eeprom or args.flash)
    
    '''
    FIXME: couldn't get I2C to work
    probably doesn't matter since expect only EEPROM on bus
    
    List of  controlRead(0xC0, 0xB0,...)
    req     uses
    0x03    fpga_r
    0x04    fpga_sig
    0x0A    i2c_r
    0x0B    eeprom_r
    0x10    flash_r
    0x20    state
    0x23    img_wh
    0x25    trig_param_r
    0x2D    int_time
    0x40    img_ctr_r
    0x51    versions
    0x80    error
    '''
    
    if alll:
        print
        print 'Versions'
        gxs.versions()
        open(os.path.join(args.dout, 'ver.bin'), 'w').write(gxs.versions(decode=False))
        
        print
        print 'FPGA signature: 0x%04X' % gxs.fpga_rsig()
        print 'State: %d' % gxs.state()
        print 'Error: %d' % gxs.error()
        print 'Trigger params: %s' % binascii.hexlify(gxs.trig_param_r())
        print 'Int time: %s' % gxs.int_time()
        print 'Img ctr: %s' % binascii.hexlify(gxs.img_ctr_r())
        
        w, h = gxs.img_wh()
        print 'Sensor dimensions: %dw x %dh' % (w, h)

        print
        print 'Dumping RAM'
        '''
        The FX2 has eight kbytes of internal program/data RAM,
        Only the internal eight kbytes and scratch pad 0.5 kbytes RAM spaces have the following access:
        
        The available RAM spaces are 8 kbytes from
        0x0000-0x1FFF (code/data) and 512 bytes from 0xE000-0xE1FF (scratch pad RAM).
        '''
        ram = gxs700_util.ram_r(dev, 0x0000, 0x10000)
        open(os.path.join(args.dout, 'ram.bin'), 'w').write(ram)
    
    if alll or args.eeprom:
        print 'Dumping EEPROM'
        eeprom = gxs.eeprom_r()
        if args.hexdump:
            util.hexdump(eeprom)
        else:
            open(os.path.join(args.dout, 'eeprom.bin'), 'w').write(eeprom)

    if alll or args.flash:
        print 'Dumping flash'
        flash = gxs.flash_r()
        if args.hexdump:
                util.hexdump(flash)
        else:
            open(os.path.join(args.dout, 'flash.bin'), 'w').write(flash)

    if alll:
        print 'Dumping register space'
        f = open(os.path.join(args.dout, 'regs.csv'), 'w')
        f.write('reg,val\n')
        # slightly faster
        if 1:
            for kbase in xrange(0x0000, 0x10000, 0x80):
                vs = gxs.fpga_rv(kbase, 0x80)
                for i, v in enumerate(vs):
                    k = kbase + i
                    f.write('0x%04X,0x%04X\n' % (k, v))    
        if 0:
            for k in xrange(0x0000, 0x10000, 0x1):
                v = gxs.fpga_r(k)
                f.write('0x%04X,0x%04X\n' % (k, v))    
    
