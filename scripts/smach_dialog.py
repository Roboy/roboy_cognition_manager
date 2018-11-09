#!/usr/bin/env python

import rospy
import smach
from smach_ros import ServiceState
import time

from roboy_communication_cognition.srv import RecognizeSpeech, Talk, TalkRequest
from rospy_tutorials.srv import AddTwoInts, AddTwoIntsRequest

# define state Bar
class Bar(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['outcome2'])

    def execute(self, userdata):
        rospy.loginfo('Executing state BAR')
        time.sleep(1)
        return 'outcome2'

class Processor(smach.State):
    def __init__(self):
        smach.State.__init__(self, input_keys = ['tts_text', 'stt_text'], outcomes=['succeeded'])

    def execute(self, userdata):
        tokens = userdata.stt_text.split()
        if "kasse" in tokens:
            rospy.loginfo("asking for kasse")
        return 'succeeded'

class RawInput(smach.State):
    def __init__(self):
        smach.State.__init__(self,  output_keys=['stt_text'], input_keys = ['tts_text', 'stt_text'], outcomes=['succeeded'])

    def execute(self,userdata):
        userdata.stt_text = raw_input()
        return 'succeeded'

def main():
    rospy.init_node('smach_dialog')
    sm = smach.StateMachine(['succeeded','aborted','preempted'])
    sm.userdata.tts_text = 'yaaas'
    sm.userdata.stt_text = 'nnooo'
    with sm:
        @smach.cb_interface(output_keys=['stt_text'])
        def stt_result_cb(userdata, result):
            userdata.stt_text = result.text
            rospy.logwarn(result.text)
            return 'succeeded'

        @smach.cb_interface(input_keys=['tts_text', 'stt_text'])
        def tts_request_cb(userdata, request):
            tts_request = TalkRequest(userdata.stt_text)
            time.sleep(1)
            return tts_request

        smach.StateMachine.add('RAW_INPUT', RawInput(),
                            transitions={'succeeded':'PROCESSOR'})

        smach.StateMachine.add('PROCESSOR', Processor(),
                            transitions={'succeeded':'RAW_INPUT'})

        smach.StateMachine.add('SYNTHESIZE_SPEECH',
                        ServiceState('/roboy/cognition/speech/synthesis/talk',
                                    Talk,
                                    request_cb = tts_request_cb,
                                    input_keys = ['tts_text', 'stt_text']),
                        transitions={'succeeded':'RECOGNIZE_SPEECH'}
                    )

        smach.StateMachine.add('BAR', Bar(),
                       transitions={'outcome2':'SYNTHESIZE_SPEECH'})

        smach.StateMachine.add('RECOGNIZE_SPEECH',
                        ServiceState('/roboy/cognition/speech/recognition',
                                    RecognizeSpeech,
                                    response_cb=stt_result_cb,
                                    output_keys=['stt_text']),
                        transitions={'succeeded':'SYNTHESIZE_SPEECH'}
                        )





        outcome = sm.execute()

if __name__ == '__main__':
    main()
