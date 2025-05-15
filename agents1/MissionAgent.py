import sys, random, enum, ast, time, csv, os
import numpy as np
import pandas as pd
from collections import Counter
from matrx import grid_world
from brains1.ArtificialBrain import ArtificialBrain
from actions1.CustomActions import *
from matrx import utils
from matrx.grid_world import GridWorld
from matrx.agents.agent_utils.state import State
from matrx.agents.agent_utils.navigator import Navigator
from matrx.agents.agent_utils.state_tracker import StateTracker
from matrx.actions.door_actions import OpenDoorAction
from matrx.actions.object_actions import GrabObject, DropObject, RemoveObject
from matrx.actions.move_actions import MoveNorth
from matrx.messages.message import Message
from matrx.messages.message_manager import MessageManager
from actions1.CustomActions import RemoveObjectTogether, CarryObjectTogether, DropObjectTogether, CarryObject, Drop
import table_api

class Phase(enum.Enum):
    INTRO = 1,
    FIND_NEXT_GOAL = 2,
    PICK_UNSEARCHED_ROOM = 3,
    PLAN_PATH_TO_VICTIM = 4,
    FOLLOW_PATH_TO_VICTIM = 5,
    TAKE_VICTIM = 6,
    PLAN_PATH_TO_DROPPOINT = 7,
    FOLLOW_PATH_TO_DROPPOINT = 8,
    DROP_VICTIM = 9 


class BaselineAgent(ArtificialBrain):
    def __init__(self, slowdown, condition, participant_id, agent_type, agent_name, human_name, my_areas, victim_order, folder):
        super().__init__(slowdown, agent_type, agent_name, folder)
        # Initialization of some relevant variables
        self._tick = None
        self._slowdown = slowdown
        self._participant_id = participant_id
        self._agent_type = agent_type
        self._human_name = human_name
        self._agent_name = agent_name
        self._folder = folder
        self._my_areas = my_areas
        self._ordered_victims = victim_order
        self._phase = Phase.INTRO
        self._room_vics = []
        self._searched_rooms = []
        self._found_victims = []
        self._collected_victims = []
        self._found_victim_logs = {}
        self._send_messages = []
        self._current_door = None
        self._team_members = []
        self._carrying_together = False
        self._remove = False
        self._goal_vic = None
        self._goal_loc = None
        self._human_loc = None
        self._distance_human = None
        self._distance_drop = None
        self._agent_loc = None
        self._todo = []
        self._answered = False
        self._to_search = []
        self._carrying = False
        self._waiting = False
        self._rescue = None
        self._recent_vic = None
        self._received_messages = []
        self._moving = False
        self._last_vic = 0
        self._condition = condition

    def initialize(self):
        # Initialization of the state tracker and navigation algorithm
        self._state_tracker = StateTracker(agent_id=self.agent_id)
        self._navigator = Navigator(agent_id=self.agent_id, action_set=self.action_set,
                                    algorithm=Navigator.A_STAR_ALGORITHM)
        #self._action_logs = pd.DataFrame(columns = ["condition","PID","agent","tick","local_time","location","vic_area","in_own_area?","action","victim","vic_drop_loc","vic_order","score","completeness","water_time"])
        if self._condition == "mission_comm" or self._condition == "mission_nocomm":
            self.log_allocation_df("agent", -1)


    def log_allocation_df(self, decided_by, change):
        allocation_log = pd.DataFrame([{"PID": self._participant_id,
                                                "condition": self._condition,
                                                "agent_type": self._agent_type,
                                                "local_time": int(time.time()),
                                                "human_areas": table_api.human_areas,
                                                "agent_areas": table_api.agent_areas,
                                                "decided_by": decided_by,
                                                "changes": change}])
        if os.path.exists(table_api.ALLOCATION_CSV):
        # Append to the file without writing the header
            allocation_log.to_csv(table_api.ALLOCATION_CSV, mode='a', header=False, index=False)
        else:
            # If the file does not exist, write the DataFrame with the header
            allocation_log.to_csv(table_api.ALLOCATION_CSV, mode='w', header=True, index=False)
        
    def log_action_df(self, state, action, victim, in_order="NA"):
        my_area =  victim["area"] in self._my_areas
        at_drop_off = victim["drop_location"] == state[self.agent_id]['location']

        new_row = {
            "condition": self._condition,
            "PID": self._participant_id,
            "agent_type": self._agent_type,
            "tick": state['World']['nr_ticks'],
            "local_time": int(time.time()),
            "location": state[self.agent_id]['location'],
            "vic_area": victim["area"],
            "in_own_area?": my_area,
            "action": action,
            "victim": victim["name"],
            "vic_drop_loc": victim["drop_location"],
            "vic_order": victim["order"],
            "at_drop_off": at_drop_off,
            "in_order": in_order,
            "score": table_api.total_score,
            "completeness": table_api.completeness,
            "water_time": table_api.time_water,
        }

        table_api.action_logs = pd.concat([table_api.action_logs, pd.DataFrame([new_row])], ignore_index=True)
        #print(table_api.action_logs)

        return True

    def filter_observations(self, state):
        # Filtering of the world state before deciding on an action 
        return state
    
    # Updating my_areas based on what is passed through server
    def set_myareas(self, new_areas):
        self._my_areas = new_areas

    def decide_on_actions(self, state):
        # Identify team members
        agent_name = state[self.agent_id]['obj_id']

        for member in state['World']['team_members']:
            if member != agent_name and member not in self._team_members:
                self._team_members.append(member)

        zones = self._get_drop_zones(state)


        # Ongoing loop until the task is terminated, using different phases for defining the agent's behavior
        while True:
            if table_api.updated_agent_areas:
                print("UPDATE AREAS", table_api.agent_areas)
                old_counts = Counter(self._my_areas)
                new_counts = Counter(table_api.agent_areas)

                # Elements that are different (symmetric difference in count)
                diff = (old_counts - new_counts) + (new_counts - old_counts)
                num_changed = sum(diff.values()) // 2  # Divide by 2 to count changes, not total excess

                self._my_areas = table_api.agent_areas
                table_api.updated_agent_areas = False

                self.log_allocation_df("human", num_changed)

                self._phase = Phase.INTRO

            if Phase.INTRO == self._phase:
                # TODO Wait untill the human starts moving before going to the next phase, otherwise remain idle
                #if not state[{'is_human_agent': True}]:
                if table_api.alloc_comm_table_triggered == True or table_api.alloc_nocomm_table_triggered == True:
                    return None, {}
                else:
                    self._phase = Phase.FIND_NEXT_GOAL
                    return None, {}
                    
            # phases: planning - update plan - go to next victim in own areas - bring vicitm to drop zone - wait for turn - drop victim

            if Phase.FIND_NEXT_GOAL == self._phase:
                print("FIND_NEXT_GOAL")
                # Definition of some relevant variables
                self._answered = False
                self._goal_vic = None
                self._moving = True

                # check following victim within agent's areas to be rescued
                for vic in self._ordered_victims[self._last_vic:]:
                    if vic['area'] in self._my_areas:
                    #  check if victim still at location
                        if state[vic['name']] != None and state[vic['name']].get('location') == vic['location']:
                            self._goal_vic = vic
                            self._phase = Phase.PLAN_PATH_TO_VICTIM
                            return Idle.__name__, {'action_duration': 10}
                        else:
                            continue
                
                return None, {}

            if Phase.PLAN_PATH_TO_VICTIM == self._phase:
                # Plan the path to a found victim using its location
                print("PLAN_PATH_TO_VICTIM", self._goal_vic['location'])
                self._navigator.reset_full()
                self._navigator.add_waypoints([self._goal_vic['location']])
                # Follow the path to the found victim
                self._phase = Phase.FOLLOW_PATH_TO_VICTIM
                return None, {}

            if Phase.FOLLOW_PATH_TO_VICTIM == self._phase:
                # Start searching for other victims if the human already rescued the target victim
                #if self._goal_vic and self._goal_vic in self._collected_victims:
                #    self._phase = Phase.FIND_NEXT_GOAL

                # Move towards the location of the found victim
                #else:
                print("FOLLOW_PATH_TO_VICTIM")
                self._state_tracker.update(state)

                action = self._navigator.get_move_action(self._state_tracker)
                # If there is a valid action, return it; otherwise, switch to taking the victim
                if action is not None:
                    return action, {}
                self._phase = Phase.TAKE_VICTIM
                return None, {}

            if Phase.TAKE_VICTIM == self._phase:
                objects = []
                for info in state.values():
                    # When the victim has to be carried by human and agent together, check whether human has arrived at the victim's location
                    if 'class_inheritance' in info and 'CollectableBlock' in info['class_inheritance'] and self._goal_vic['name'] in info['name']:
                        if info['location'] != None and utils.get_distance(info['location'],state[self.agent_id]['location']) < 1:

                            objects.append(info)

                            print("Taking victim")

                            self._phase = Phase.PLAN_PATH_TO_DROPPOINT

                            self._collected_victims.append(self._goal_vic)
                            self._carrying = True

                            # log that agent picked up victim
                            if self._condition != "tutorial":
                                self.log_action_df(state,"take_victim",self._goal_vic)

                            return CarryObject.__name__, {'object_id': self._goal_vic['name'], 'human_name': self._human_name}
                        else:
                            self._phase = Phase.FIND_NEXT_GOAL
                
                return None, {}
                
            if Phase.PLAN_PATH_TO_DROPPOINT == self._phase:
                print("PLAN_PATH_TO_DROPPOINT", self._goal_vic['drop_location'])
                self._navigator.reset_full()
                # Plan the path to the drop zone
                self._navigator.add_waypoints([self._goal_vic['drop_location']])
                # Follow the path to the drop zone
                self._phase = Phase.FOLLOW_PATH_TO_DROPPOINT

                return None, {}

            if Phase.FOLLOW_PATH_TO_DROPPOINT == self._phase:
                print("FOLLOW_PATH_TO_DROPPOINT")
                # Communicate that the agent is transporting a mildly injured victim alone to the drop zone
                self._state_tracker.update(state)
                # Follow the path to the drop zone
                action = self._navigator.get_move_action(self._state_tracker)
                #print("action", action)
                if action is not None:
                    return action, {}
                
                self._phase = Phase.DROP_VICTIM

                return None, {}


            if Phase.DROP_VICTIM == self._phase:
               # check if the agent can drop the victim
                # i.e. check if all previous victims are in place
                   # Get the order of the last victim
                
                if self._goal_vic != None:
                    last_order = int(self._goal_vic['name'][7:-1])

                    # Check if all previous victims (1 to last_order - 1) are at their goal locations
                    self._waiting = False
                    expected_location = None

                    for i in range(1, last_order):
                        victim_name = f"victim_{i}_"
                        #victim not in the world at the moment, probably being carried by human
                        if state[victim_name] is None:
                            return None, {}

                        actual_location = state[victim_name].get('location')

                        for index, item in enumerate(self._ordered_victims):
                            if item.get("name") == victim_name:
                                expected_location = item.get("drop_location")

                                break

                        if expected_location != None and actual_location != expected_location:
                            expected_location = None
                            self._waiting = True
                            break

                    # otherwise, drop the victim
                    if not self._waiting:
                        # Identify the next target victim to rescue
                        self._phase = Phase.FIND_NEXT_GOAL

                        # update local state
                        self._last_vic = self._goal_vic['order']
                        self._tick = state['World']['nr_ticks']
                        self._carrying = False

                        table_api.agent_vics_saved_abs += 1
                        table_api.total_score += 5

                        # Log action
                        if self._condition != "tutorial":
                            self.log_action_df(state,"drop_victim",self._goal_vic, True)
                            
                                                
                        # Drop the victim on the correct location on the drop zone
                        return Drop.__name__, {'human_name': self._human_name}
                
                return None, {}

    def _get_drop_zones(self, state):
        '''
        @return list of drop zones (their full dict), in order (the first one is the
        place that requires the first drop)
        '''
        places = state[{'is_goal_block': True}]
        places.sort(key=lambda info: info['location'][1])
        zones = []
        for place in places:
            if place['drop_zone_nr'] == 0:
                zones.append(place)
        return zones

    def _getClosestRoom(self, state, objs, currentDoor):
        '''
        calculate which area is closest to the agent's location
        '''
        agent_location = state[self.agent_id]['location']
        locs = {}
        for obj in objs:
            locs[obj] = state.get_room_doors(obj)[0]['location']
        dists = {}
        for room, loc in locs.items():
            if currentDoor != None:
                dists[room] = utils.get_distance(currentDoor, loc)
            if currentDoor == None:
                dists[room] = utils.get_distance(agent_location, loc)

        return min(dists, key=dists.get)

    def _efficientSearch(self, tiles):
        '''
        efficiently transverse areas instead of moving over every single area tile
        '''
        x = []
        y = []
        for i in tiles:
            if i[0] not in x:
                x.append(i[0])
            if i[1] not in y:
                y.append(i[1])
        locs = []
        for i in range(len(x)):
            if i % 2 == 0:
                locs.append((x[i], min(y)))
            else:
                locs.append((x[i], max(y)))
        return locs
