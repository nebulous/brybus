#!/usr/bin/python

#does a scan of all tables on all devices

import time
scriptstart =  time.time()

import brybus
import bryqueue
import bryfunc
ByteToHex = bryfunc.ByteToHex
HexToByte = bryfunc.HexToByte

#setup the stream and bus
s = brybus.stream('S','/dev/ttyUSB0')
b = brybus.bus(s)
phase = 0

#loop forever
while(1):

  #phase 0 reads the bus for 10 seconds to determine a list of devices
  if phase==0:
    #scan devices for X seconds - exit loop by setting phase=1
    if 'ph1_time' in locals():
      if time.time() - ph1_time > 10:
        phase=1        
        #uncomment the next line to force items into the device list
        #devices.append("XXXX")
        print "ending phase 0"
        print "Devices:",devices
    #if variables are not setup do some init stuff one time
    else:
      ph1_time = time.time()
      print "starting phase 0"
      devices=[]
    #loop to read a frame and build a list of devices
    f = brybus.frame(b.read(),"B") 
    if f.src not in devices:
      devices.append(f.src)

  #use device list to build a queue of all possible tables, scan them all
  if phase==1:
    #if the initial setup is done, scan it (normal write/read loop)
    if 'ph1_q' in locals():
      #write
      w = b.write(ph1_q.writeframe())
      if w==1:
        print "write", ph1_q.printstatus(), ByteToHex(ph1_q.writeframe())
      if w==2:
        print "pause"
      #read and check frame      
      f = brybus.frame(b.read(),"B")
      #only print it if it followed a write
      if w==1:
        print f.dst,f.src,f.len,f.func,f.data,f.crc
      ph1_q.checkframe(f)
      #test for end of phase, set phase=2 to break      
      if ph1_q.writeframe() == '':
        phase=2           
        print "ending phase 1"
    #initial setup for the queue
    else:  
      print "starting phase 1"
      ph1_q = bryqueue.writequeue()
      for d in devices:
        for t in range(1,64): #shorten this for testing - set back to 1-64
          reg = '00' + "{0:02X}".format(t) + '01' 
          wf = brybus.frame(reg,'C',d,'3001','0B')
          ph1_q.pushframe(wf)
      print "phase 1 queue built"
      ph1_q.printqueue()
                      
  #use the output of the scan to build a list of valid devices and tables
  if phase==2:
    #show all data from phase 2 for debugging
    ph1_q.printqueue()
    tables=[]
    
    print "==start table definition variable=="
    #show all queue items where there was not an error - info only
    for k,v in ph1_q.queue.iteritems():
      if v.response.func != '15':
       print v.frame.dst, v.frame.data[2:4], v.response.data[30:32]
    

    print "==start all valid table row combinations =="    
    #write csv to console to build final output
    for k,v in ph1_q.queue.iteritems():
      #for responses that were not an error
      if v.response.func != '15':
        #use the first part of the table definition on each row to output 
        output = ''
        output += v.frame.dst + ','
        output += v.frame.data[2:4] + ','
        output += v.response.data[6:10] + ','
        output += v.response.data[10:26].decode('hex') + ','
        output += v.response.data[26:30] + ','
        output += v.response.data[30:32] + ','
        #loop over the end of the table definition to define the rows in the table
        for r in range(0,int(v.response.data[30:32],16)):
          thisrow = 32+4*r
          #if 0000 is the row definition, it does not exist, so don't print it
          if v.response.data[thisrow:thisrow+4] != '0000':
            row_output = "{0:02X}".format(r+1)+ ','
            row_output += v.response.data[thisrow:thisrow+2] + ','
            row_output += v.response.data[thisrow+2:thisrow+4]
            print output+row_output

    print "Seconds Elapsed:",(time.time()-scriptstart)
    exit()
