import os
import subprocess
import ros
import rosbag
import rospy
import time
import psutil
import roslaunch
import rospy
import signal

scenes = ['Town01', 'Town02', 'Town03', 'Town04', 'Town05', 'Town06', 'Town07']

MAP_PATH = '/Game/Carla/Maps/'
CARLA_SERVER = os.environ['CARLA_SERVER']
CARLA_ROOT = os.environ['CARLA_ROOT']
CARLA_PYTHONAPI_PATH = os.environ['CARLA_ROOT'] + 'PythonAPI/example'  
DATA_COLLECTION_TIME = 1 # 5 mins
DATASET_FOLDER = '/mnt/data/Datasets/Carla/segbags'

class DataCollection():
    def __init__(self):
        self.server_proc = None
        self.client_proc = None
        self.rosbag_proc = None
    
    @staticmethod
    def _stop_proc(proc):
        if proc is not None:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        return None
        # outs, errs = proc.communicate()

    @staticmethod
    def _check_proc(proc):
        if proc is not None:
            print('Stopping previous server [PID=%s]', proc.pid)
            proc.kill()
            proc = None
            # outs, errs = proc.communicate()
        return None

    @staticmethod
    def terminate_ros_node(self, s):
        # Adapted from http://answers.ros.org/question/10714/start-and-stop-rosbag-within-a-python-script/
        list_cmd = subprocess.Popen("rosnode list", shell=True, stdout=subprocess.PIPE)
        list_output = list_cmd.stdout.read()
        retcode = list_cmd.wait()
        assert retcode == 0, "List command returned %d" % retcode
        for str in list_output.split("\n"):
            if (str.startswith(s)):
                os.system("rosnode kill " + str)

    def run(self):
        try:
            for town in scenes:
                self.server_proc = self._check_proc(self.server_proc)
                carla_server_binary = CARLA_SERVER + ' ' + MAP_PATH + town
                exec_command = "{} -benchmark -fps=20 -quality-level=Epic >/dev/null".format(carla_server_binary)
                print('Server Started')
                self.server_proc = subprocess.Popen(exec_command, shell=True)
                # server_outs, server_errs = self.server_proc.communicate()
                time.sleep(30)

                self.client_proc = self._check_proc(self.client_proc)
                print('Client Started')
                self.client_proc = subprocess.Popen(['python','multiple_sensor.py','-l','-d','-s','--res','300x300','-a'], stdout=subprocess.PIPE, shell=False)
                # client_outs, client_errs = self.client_proc.communicate()
                # time.sleep(10)

                # rospy.init_node('en_Mapping', anonymous=True)
                print("Launch file started")
                # exec(open("/mnt/data/Workspaces/delta_ws/devel/setup.bash").read())
                uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
                roslaunch.configure_logging(uuid)
                cli_args = ['/mnt/data/Workspaces/delta_ws/src/ros-bridge/carla_ros_bridge/launch/carla_ros_bridge.launch','rosbag_fname:=Town']
                roslaunch_args = cli_args[1:]
                roslaunch_file = [(roslaunch.rlutil.resolve_launch_arguments(cli_args)[0])]
                launch = roslaunch.parent.ROSLaunchParent(uuid, roslaunch_file)
                launch.start()
                
                self.rosbag_proc = self._check_proc(self.rosbag_proc)
                print("Rosbag started")
                self.rosbag_proc = subprocess.Popen(['rosbag record -a -O '+str(town)+str('_01')], stdin=subprocess.PIPE, shell=True, cwd=DATASET_FOLDER)

                time.sleep(DATA_COLLECTION_TIME*60)
                time.sleep(20)

                self.terminate_ros_node(self,"/record")
                launch.shutdown()
                self.client_proc = self._stop_proc(self.client_proc)
                self.server_proc = self._stop_proc(self.server_proc)
                time.sleep(20)

        except KeyboardInterrupt:
            self.terminate_ros_node(self, "/record")
            launch.shutdown()
            self.client_proc = self._stop_proc(self.client_proc)
            self.server_proc = self._stop_proc(self.server_proc)
            return
        except:
            print('Program Closing')
            self.terminate_ros_node(self, "/record")
            launch.shutdown()
            self.client_proc = self._stop_proc(self.client_proc)
            self.server_proc = self._stop_proc(self.server_proc)
            return

if __name__ == "__main__":
    data = DataCollection()
    data.run()
    
