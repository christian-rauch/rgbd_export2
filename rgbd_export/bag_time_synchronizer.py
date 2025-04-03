from message_filters import ApproximateTimeSynchronizer

# custom ApproximateTimeSynchronizer
class BagTimeSynchronizer(ApproximateTimeSynchronizer):
    def connectInput(self, fs):
        # manually set up one queue per topic
        # https://www.youtube.com/watch?v=3KvWwJ6sh5s
        self.queues = [{} for f in fs]
        self.queue_index = {t: i for (i, t) in enumerate(fs)}

    def add_msg(self, msg, topic):
        self.add(msg, self.queues[self.queue_index[topic]])
