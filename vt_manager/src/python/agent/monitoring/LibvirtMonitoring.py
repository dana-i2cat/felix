#!/usr/bin/python -u
#
#
#
#################################################################################
# Start off by implementing a general purpose event loop for anyones use
#################################################################################

import sys
import getopt
import os
import libvirt
import select
import errno
import time
import threading
import logging

from utils.Logger import Logger

logger = Logger.getLogger()
#
# This general purpose event loop will support waiting for file handle
# I/O and errors events, as well as scheduling repeatable timers with
# a fixed interval.
#
# It is a pure python implementation based around the poll() API
#
class virEventLoopPure:
    # This class contains the data we need to track for a
    # single file handle
    class virEventLoopPureHandle:
        def __init__(self, handle, fd, events, cb, opaque):
            self.handle = handle
            self.fd = fd
            self.events = events
            self.cb = cb
            self.opaque = opaque

        def get_id(self):
            return self.handle

        def get_fd(self):
            return self.fd

        def get_events(self):
            return self.events

        def set_events(self, events):
            self.events = events

        def dispatch(self, events):
            self.cb(self.handle,
                    self.fd,
                    events,
                    self.opaque[0],
                    self.opaque[1])

    # This class contains the data we need to track for a
    # single periodic timer
    class virEventLoopPureTimer:
        def __init__(self, timer, interval, cb, opaque):
            self.timer = timer
            self.interval = interval
            self.cb = cb
            self.opaque = opaque
            self.lastfired = 0

        def get_id(self):
            return self.timer

        def get_interval(self):
            return self.interval

        def set_interval(self, interval):
            self.interval = interval

        def get_last_fired(self):
            return self.lastfired

        def set_last_fired(self, now):
            self.lastfired = now

        def dispatch(self):
            self.cb(self.timer,
                    self.opaque[0],
                    self.opaque[1])


    def __init__(self):
        self.poll = select.poll()
        self.pipetrick = os.pipe()
        self.nextHandleID = 1
        self.nextTimerID = 1
        self.handles = []
        self.timers = []
        self.quit = False

        # The event loop can be used from multiple threads at once.
        # Specifically while the main thread is sleeping in poll()
        # waiting for events to occur, another thread may come along
        # and add/update/remove a file handle, or timer. When this
        # happens we need to interrupt the poll() sleep in the other
        # thread, so that it'll see the file handle / timer changes.
        #
        # Using OS level signals for this is very unreliable and
        # hard to implement correctly. Thus we use the real classic
        # "self pipe" trick. A anonymous pipe, with one end registered
        # with the event loop for input events. When we need to force
        # the main thread out of a poll() sleep, we simple write a
        # single byte of data to the other end of the pipe.
        logger.debug("Self pipe watch %d write %d" %(self.pipetrick[0], self.pipetrick[1]))
        self.poll.register(self.pipetrick[0], select.POLLIN)



    # Calculate when the next timeout is due to occurr, returning
    # the absolute timestamp for the next timeout, or 0 if there is
    # no timeout due
    def next_timeout(self):
        next = 0
        for t in self.timers:
            last = t.get_last_fired()
            interval = t.get_interval()
            if interval < 0:
                continue
            if next == 0 or (last + interval) < next:
                next = last + interval

        return next

    # Lookup a virEventLoopPureHandle object based on file descriptor
    def get_handle_by_fd(self, fd):
        for h in self.handles:
            if h.get_fd() == fd:
                return h
        return None

    # Lookup a virEventLoopPureHandle object based on its event loop ID
    def get_handle_by_id(self, handleID):
        for h in self.handles:
            if h.get_id() == handleID:
                return h
        return None


    # This is the heart of the event loop, performing one single
    # iteration. It asks when the next timeout is due, and then
    # calcuates the maximum amount of time it is able to sleep
    # for in poll() pending file handle events.
    #
    # It then goes into the poll() sleep.
    #
    # When poll() returns, there will zero or more file handle
    # events which need to be dispatched to registered callbacks
    # It may also be time to fire some periodic timers.
    #
    # Due to the coarse granularity of schedular timeslices, if
    # we ask for a sleep of 500ms in order to satisfy a timer, we
    # may return upto 1 schedular timeslice early. So even though
    # our sleep timeout was reached, the registered timer may not
    # technically be at its expiry point. This leads to us going
    # back around the loop with a crazy 5ms sleep. So when checking
    # if timeouts are due, we allow a margin of 20ms, to avoid
    # these pointless repeated tiny sleeps.
    def run_once(self):
        sleep = -1
        next = self.next_timeout()
        #logger.debug("Next timeout due at %d" % next)
        if next > 0:
            now = int(time.time() * 1000)
            if now >= next:
                sleep = 0
            else:
                sleep = (next - now) / 1000.0

        #logger.debug("Poll with a sleep of %d" % sleep)
        events = self.poll.poll(sleep)

        # Dispatch any file handle events that occurred
        for (fd, revents) in events:
            # See if the events was from the self-pipe
            # telling us to wakup. if so, then discard
            # the data just continue
            if fd == self.pipetrick[0]:
                data = os.read(fd, 1)
                continue

            h = self.get_handle_by_fd(fd)
            if h:
                #logger.debug("Dispatch fd %d handle %d events %d" % (fd, h.get_id(), revents))
                h.dispatch(self.events_from_poll(revents))

        now = int(time.time() * 1000)
        for t in self.timers:
            interval = t.get_interval()
            if interval < 0:
                continue

            want = t.get_last_fired() + interval
            # Deduct 20ms, since schedular timeslice
            # means we could be ever so slightly early
            if now >= (want-20):
                #logger.debug("Dispatch timer %d now %s want %s" % (t.get_id(), str(now), str(want)))
                t.set_last_fired(now)
                t.dispatch()


    # Actually the event loop forever
    def run_loop(self):
        self.quit = False
        while not self.quit:
            self.run_once()

    def interrupt(self):
        os.write(self.pipetrick[1], 'c')


    # Registers a new file handle 'fd', monitoring  for 'events' (libvirt
    # event constants), firing the callback  cb() when an event occurs.
    # Returns a unique integer identier for this handle, that should be
    # used to later update/remove it
    def add_handle(self, fd, events, cb, opaque):
        handleID = self.nextHandleID + 1
        self.nextHandleID = self.nextHandleID + 1

        h = self.virEventLoopPureHandle(handleID, fd, events, cb, opaque)
        self.handles.append(h)

        self.poll.register(fd, self.events_to_poll(events))
        self.interrupt()

        logger.debug("Add handle %d fd %d events %d" % (handleID, fd, events))

        return handleID

    # Registers a new timer with periodic expiry at 'interval' ms,
    # firing cb() each time the timer expires. If 'interval' is -1,
    # then the timer is registered, but not enabled
    # Returns a unique integer identier for this handle, that should be
    # used to later update/remove it
    def add_timer(self, interval, cb, opaque):
        timerID = self.nextTimerID + 1
        self.nextTimerID = self.nextTimerID + 1

        h = self.virEventLoopPureTimer(timerID, interval, cb, opaque)
        self.timers.append(h)
        self.interrupt()

        logger.debug("Add timer %d interval %d" % (timerID, interval))

        return timerID

    # Change the set of events to be monitored on the file handle
    def update_handle(self, handleID, events):
        h = self.get_handle_by_id(handleID)
        if h:
            h.set_events(events)
            self.poll.unregister(h.get_fd())
            self.poll.register(h.get_fd(), self.events_to_poll(events))
            self.interrupt()

            #logger.debug("Update handle %d fd %d events %d" % (handleID, h.get_fd(), events))

    # Change the periodic frequency of the timer
    def update_timer(self, timerID, interval):
        for h in self.timers:
            if h.get_id() == timerID:
                h.set_interval(interval);
                self.interrupt()

                #logger.debug("Update timer %d interval %d"  % (timerID, interval))
                break

    # Stop monitoring for events on the file handle
    def remove_handle(self, handleID):
        handles = []
        for h in self.handles:
            if h.get_id() == handleID:
                self.poll.unregister(h.get_fd())
                logger.debug("Remove handle %d fd %d" % (handleID, h.get_fd()))
            else:
                handles.append(h)
        self.handles = handles
        self.interrupt()

    # Stop firing the periodic timer
    def remove_timer(self, timerID):
        timers = []
        for h in self.timers:
            if h.get_id() != timerID:
                timers.append(h)
                logger.debug("Remove timer %d" % timerID)
        self.timers = timers
        self.interrupt()

    # Convert from libvirt event constants, to poll() events constants
    def events_to_poll(self, events):
        ret = 0
        if events & libvirt.VIR_EVENT_HANDLE_READABLE:
            ret |= select.POLLIN
        if events & libvirt.VIR_EVENT_HANDLE_WRITABLE:
            ret |= select.POLLOUT
        if events & libvirt.VIR_EVENT_HANDLE_ERROR:
            ret |= select.POLLERR;
        if events & libvirt.VIR_EVENT_HANDLE_HANGUP:
            ret |= select.POLLHUP;
        return ret

    # Convert from poll() event constants, to libvirt events constants
    def events_from_poll(self, events):
        ret = 0;
        if events & select.POLLIN:
            ret |= libvirt.VIR_EVENT_HANDLE_READABLE;
        if events & select.POLLOUT:
            ret |= libvirt.VIR_EVENT_HANDLE_WRITABLE;
        if events & select.POLLNVAL:
            ret |= libvirt.VIR_EVENT_HANDLE_ERROR;
        if events & select.POLLERR:
            ret |= libvirt.VIR_EVENT_HANDLE_ERROR;
        if events & select.POLLHUP:
            ret |= libvirt.VIR_EVENT_HANDLE_HANGUP;
        return ret;


###########################################################################
# Now glue an instance of the general event loop into libvirt's event loop
###########################################################################

# This single global instance of the event loop wil be used for
# monitoring libvirt events
eventLoop = virEventLoopPure()

# This keeps track of what thread is running the event loop,
# (if it is run in a background thread)
eventLoopThread = None


# These next set of 6 methods are the glue between the official
# libvirt events API, and our particular impl of the event loop
#
# There is no reason why the 'virEventLoopPure' has to be used.
# An application could easily may these 6 glue methods hook into
# another event loop such as GLib's, or something like the python
# Twisted event framework.

class LibvirtMonitor:
    
    @staticmethod
    def virEventAddHandleImpl(fd, events, cb, opaque):
        global eventLoop
        return eventLoop.add_handle(fd, events, cb, opaque)

    @staticmethod
    def virEventUpdateHandleImpl(handleID, events):
        global eventLoop
        return eventLoop.update_handle(handleID, events)

    @staticmethod
    def virEventRemoveHandleImpl(handleID):
        global eventLoop
        return eventLoop.remove_handle(handleID)

    @staticmethod
    def virEventAddTimerImpl(interval, cb, opaque):
        global eventLoop
        return eventLoop.add_timer(interval, cb, opaque)

    @staticmethod
    def virEventUpdateTimerImpl(timerID, interval):
        global eventLoop
        return eventLoop.update_timer(timerID, interval)

    @staticmethod
    def virEventRemoveTimerImpl(timerID):
        global eventLoop
        return eventLoop.remove_timer(timerID)

    # This tells libvirt what event loop implementation it
    # should use
    @staticmethod
    def virEventLoopPureRegister():
        libvirt.virEventRegisterImpl(LibvirtMonitor.virEventAddHandleImpl,
                                     LibvirtMonitor.virEventUpdateHandleImpl,
                                     LibvirtMonitor.virEventRemoveHandleImpl,
                                     LibvirtMonitor.virEventAddTimerImpl,
                                     LibvirtMonitor.virEventUpdateTimerImpl,
                                     LibvirtMonitor.virEventRemoveTimerImpl)
 
    # Directly run the event loop in the current thread
    @staticmethod
    def virEventLoopPureRun():
        global eventLoop
        eventLoop.run_loop()

    # Spawn a background thread to run the event loop
    @staticmethod
    def virEventLoopPureStart():
        global eventLoopThread
        LibvirtMonitor.virEventLoopPureRegister()
        eventLoopThread = threading.Thread(target=LibvirtMonitor.virEventLoopPureRun, name="libvirtEventLoop")
        eventLoopThread.setDaemon(True)
        eventLoopThread.start()

	
    @staticmethod
    def initialize():

        LibvirtMonitor.virEventLoopPureStart()    
        logging.info('Libvirt version installed: %d' %(libvirt.getVersion()))
        vc = libvirt.open(None) #XXX: maybe could it be xen:/// but callbacks will only be registered for XEN domain
	vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, LifeCycleEventCallbacks, None)

    
##########################################################################
# Everything that now follows is a simple demo of domain lifecycle events
##########################################################################
def eventToString(event):
    logger.debug("event = " + str(event))
    eventStrings = ( "Defined",
                     "Undefined",
                     "Started",
                     "Suspended",
                     "Resumed",
                     "Stopped" );
    if event < 0 or event >= len(eventStrings):
        return "UNKNOWN"
    return eventStrings[event];

def detailToString(event, detail):
    logger.debug("event = " + str(event) + ", detail = " + str(detail))
    eventStrings = (
        ( "Added", "Updated" ),
        ( "Removed", ),
        ( "Booted", "Migrated", "Restored", "Snapshot" ),
        ( "Paused", "Migrated", "IOError", "Watchdog" ),
        ( "Unpaused", "Migrated"),
        ( "Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot")
        )
    if event < 0 or event >= len(eventStrings):
        return "UNKNOWN"
    return eventStrings[event][detail]


from communications.XmlRpcClient import XmlRpcClient

def LifeCycleEventCallbacks (conn, dom, event, detail, opaque):
    liblog = open('/opt/ofelia/oxa/log/libvirtmonitor.log','a')
    log =  "Libvirt Monitoring: Domain %s(%s) with uuid %s  %s %s\n" % (dom.name(), dom.ID(),
								        dom.UUIDString(),
                                                                        eventToString(event),
                                                                        detailToString(event, detail))
    liblog.write(log)
    try:
    	XmlRpcClient.sendAsyncMonitoringLibvirtVMsInfo('callback','SUCCESS',[[dom.UUIDString(),dom.name()]],eventToString(event)) 
    except Exception as e:
	raise e
