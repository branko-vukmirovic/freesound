import zmq, time, sys, json, threading


class Messenger():

    ctxs = {}
    resolver = False
    initialized = False

    @classmethod
    def call_service(cls, address, data, timeout=60):
        t = threading.currentThread()
        if t in cls.ctxs:
            tctx = cls.ctxs[t]
            ctx = tctx['ctx']
            socket = tctx['socket']
        else:
            # create new context for thread
            ctx = zmq.Context()
            socket = False
            tctx = {'ctx': ctx, 'socket': socket}
            cls.ctxs[t] = tctx
            # clean up contexts for threads that are not running anymore
            for thr in cls.ctxs.keys():
                if not thr.isAlive():
                    try:
                        del cls.ctxs[thr]
                    except:
                        pass
        if not (socket and not socket.closed):
            socket = ctx.socket(zmq.REQ)
            tctx['socket'] = socket
            socket.connect(address)
            time.sleep(0.5) # allow socket to connect

        # socket is set up, let's use s as a shorthand
        s = socket
        poller = zmq.Poller()
        poller.register(s, zmq.POLLIN|zmq.POLLOUT)
        # sending
        try:
            # relying on correct behaviour of zeromq's poll here, needs zeromq 2.1.6
            socks = dict(poller.poll(timeout)) # this shouldn't time out!
            assert socks.has_key(s)
            assert socks[s] == zmq.POLLOUT
            s.send(json.dumps(data))
            # receiving
            try:
                socks = dict(poller.poll(timeout))
                assert socks.has_key(s)
                assert socks[s] == zmq.POLLIN
                msg = s.recv()
            except AssertionError, e:
                s.close()
                error = 'Could not receive response from %s (%s).' % (address, str(e))
                raise Exception(error)
        except AssertionError, e:
            s.close()
            error = 'Could not send message to %s.' % address
            raise Exception(error)

        if msg == '':
            return None

        msg_obj = json.loads(msg)
        if 'exception' in msg_obj and msg_obj['exception'] == True:
            raise Exception('Received an exception from service %s: \n\t%s' % (address, msg_obj['info']))
        else:
            return msg_obj


global messenger
try:
    print messenger
except:
    messenger = 'This should never be printed!'
    messenger = Messenger()
