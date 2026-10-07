"""Pinned backend with lossless query transport receipts; no protocol changes."""
from experimental_native_recall.backend import Backend


class RecordedBackend(Backend):
    def query(self,*args,**kwargs):
        process=self.process;requests=[];responses=[]
        if process is None:return super().query(*args,**kwargs)
        send,receive=process.send,process.receive
        def sent(data):
            requests.append(data.decode('ascii'));return send(data)
        def received(prefix):
            lines=receive(prefix);responses.extend(lines);return lines
        process.send=sent;process.receive=received;offset=len(self.events)
        try:return super().query(*args,**kwargs)
        finally:
            process.send=send;process.receive=receive
            # Including failed/incomplete responses; a query-bound answer has
            # zero transport bytes and must not claim a helper invocation.
            receipt=dict(requests=requests,response_lines=responses,
                request_bytes=sum(len(x.encode('ascii')) for x in requests),
                response_bytes=sum(len(x.encode('ascii'))+1 for x in responses))
            for event in self.events[offset:]:event['transport']=receipt
            self.costs['query_request_bytes']+=receipt['request_bytes']
            self.costs['query_response_bytes']+=receipt['response_bytes']
