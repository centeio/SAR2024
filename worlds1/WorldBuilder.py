import os
import sys
import numpy as np
import itertools
from collections import OrderedDict
from itertools import product
from matrx import WorldBuilder
from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction, GrabObject
from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest
from matrx.agents import AgentBrain, HumanAgentBrain, SenseCapability
from matrx.grid_world import GridWorld, AgentBody
from actions1.CustomActions import RemoveObjectTogether, DropObject, Idle, CarryObject, Drop, CarryObjectTogether, DropObjectTogether
from matrx.actions.object_actions import RemoveObject
from matrx.objects import EnvObject
from matrx.world_builder import RandomProperty
from matrx.goals import WorldGoal
from agents1.OfficialAgent import BaselineAgent
from agents1.TutorialAgent import TutorialAgent
from actions1.CustomActions import RemoveObjectTogether
from brains1.HumanBrain import HumanBrain
from loggers.ActionLogger import ActionLoggerV2
from datetime import datetime

random_seed = 1
verbose = False
# Tick duration determines the speed of the world. A tick duration of 0.1 means 10 ticks are executed in a second. 
# You can speed up or slow down the world by changing this value without changing behavior. Leave this value at 0.1 during evaluations.
tick_duration = 0.1
# Define the keyboarc controls for the human agent
key_action_map = {
        'ArrowUp': MoveNorth.__name__,
        'ArrowRight': MoveEast.__name__,
        'ArrowDown': MoveSouth.__name__,
        'ArrowLeft': MoveWest.__name__,
        'q': CarryObject.__name__,
        'w': Drop.__name__,
        'd': RemoveObjectTogether.__name__,
        'a': CarryObjectTogether.__name__,
        's': DropObjectTogether.__name__,
        'e': RemoveObject.__name__,
    }

# Some settings
nr_rooms = 9
wall_color = "#464646"
background_color = "#9c5a3c"
drop_off_color = "#1F262A"
object_size = 0.9
nr_teams = 1
agents_per_team = 2
human_agents_per_team = 1
agent_sense_range = 2  # the range with which agents detect other agents. Do not change this value.
object_sense_range = 1  # the range with which agents detect blocks. Do not change this value.
other_sense_range = np.inf  # the range with which agents detect other objects (walls, doors, etc.). Do not change this value.
fov_occlusion = True

# Add the drop zones to the world
def add_drop_off_zones(builder, task_type):
    if task_type == "mission_1":
        nr_drop_zones = 1
        for nr_zone in range(nr_drop_zones):
            builder.add_area((16,9), width=3, height=2, name=f"Drop off {nr_zone}", visualize_opacity=0.5, visualize_colour=drop_off_color, drop_zone_nr=nr_zone, is_drop_zone=True, is_goal_block=False, is_collectable=False) 
  
# Add the agents to the world
def add_agents(builder, condition, task_type, name, folder):

    for team in range(nr_teams):
        team_name = f"Team {team}"
        # Add the artificial agents based on condition
        nr_agents = agents_per_team - human_agents_per_team
        for agent_nr in range(nr_agents):
            if task_type=="mission_1":
                brain = BaselineAgent(slowdown=8, condition=condition, name=name, folder=folder) # Slowdown makes the agent a bit slower, do not change value during evaluations
                loc = (17,9)
            builder.add_agent(loc, brain, team=team_name, name="RescueBot",customizable_properties = ['score'], score=0, is_traversable=True, img_name="/images/robot-final4.svg")

        # Add human agents based on condition, do not change human brain values
        for human_agent_nr in range(human_agents_per_team):
            brain = HumanBrain(max_carry_objects=1, grab_range=1, drop_range=0, remove_range=1, fov_occlusion=fov_occlusion, strength=condition, name=name)
            loc = (17,10)
            builder.add_human_agent(loc, brain, team=team_name, name=name, key_action_map=key_action_map, is_traversable=True, img_name="/images/rescue-man-final3.svg", visualize_when_busy=True)

# Create the world
def create_builder(task_type, condition, name, folder):
    # Set numpy's random generator
    np.random.seed(random_seed)
    # Create the collection goal
    goal = CollectionGoal(max_nr_ticks=np.inf)
    # Create the world builder
    if task_type=="mission_1":
        builder = WorldBuilder(shape=[20,20], tick_duration=tick_duration, run_matrx_api=True, run_matrx_visualizer=False, verbose=verbose, simulation_goal=goal, visualization_bg_clr=background_color)
        # builder = WorldBuilder(shape=[19,19], tick_duration=tick_duration, run_matrx_api=True,random_seed=random_seed, run_matrx_visualizer=False, verbose=verbose, simulation_goal=goal, visualization_bg_clr='#9a9083')

    # Add all areas and objects to the tutorial world
    if task_type == "mission_1":
        builder.add_room(top_left_location=(0, 0), width=20, height=20, name="world_bounds", wall_visualize_colour="#546d8e")
        
        builder.add_room(top_left_location=(1,1), width=7, height=4, name='area A1', door_locations=[(2,4),(3,4),(4,4),(5,4)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_opacity=0.0, door_open_colour=background_color)
        builder.add_room(top_left_location=(1,5), width=4, height=3, name='area A2', door_locations=[(2,5),(3,5),(4,5)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)

        builder.add_room(top_left_location=(12,1), width=7, height=4, name='area B1', door_locations=[(14,4),(15,4),(16,4),(17,4)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)
        builder.add_room(top_left_location=(15,5), width=4, height=3, name='area B2', door_locations=[(15,5),(16,5),(17,5)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)

        builder.add_room(top_left_location=(1,15), width=7, height=4, name='area C1', door_locations=[(2,15),(3,15),(4,15),(5,15)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)
        builder.add_room(top_left_location=(1,12), width=4, height=3, name='area C2', door_locations=[(2,14),(3,14),(4,14)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)
        
        builder.add_room(top_left_location=(12,15), width=7, height=4, name='area D1', door_locations=[(14,15),(15,15),(16,15),(17,15)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)
        builder.add_room(top_left_location=(15,12), width=4, height=3, name='area D2', door_locations=[(15,14),(16,14),(17,14)],doors_open=True, wall_visualize_colour=wall_color, with_area_tiles=True, area_visualize_colour=background_color,area_visualize_opacity=0.0,door_open_colour=background_color)

        builder.add_object((3,3),'dog A1', callable_class=CollectableBlock, visualize_shape='img',img_name="/images/mildly injured dog.svg")
        builder.add_object((3,5),'dog A2', callable_class=CollectableBlock, visualize_shape='img',img_name="/images/mildly injured dog.svg")
        builder.add_object((5,3),'dog A2', callable_class=CollectableBlock, visualize_shape='img',img_name="/images/mildly injured dog.svg")


    # Create folders where the logs are stored during the official condition
        # current_exp_folder = datetime.now().strftime("exp_"+condition+"_at_time_%Hh-%Mm-%Ss_date_%dd-%mm-%Yy")
        # logger_save_folder = os.path.join("logs", current_exp_folder)
        # builder.add_logger(ActionLoggerV2, log_strategy=1, save_path=logger_save_folder, file_name_prefix="actions_")
        
    # Add all area and objects to the official world
        water = [(x,8) for x in list(range(1,4))] + [(x,9) for x in list(range(1,8))] + [(x,10) for x in list(range(1,11))] + \
                [(x,11) for x in list(range(1,19))] + [(x,12) for x in list(range(5,15))] + [(x,13) for x in list(range(5,15))] + \
                [(x,14) for x in list(range(5,15))] + [(x,y) for x in list(range(8,12)) for y in list(range(15,19))]
               # [(x,y) for x in list(range(2,6)) for y in list(range(15,18))] + [(x,y) for x in list(range(14,18)) for y in list(range(15,18))] + \
               # [(6,16),(6,17),(13,16),(13,17)] + + [(x,13) for x in list(range(2,4))] + [(x,13) for x in list(range(16,18))]
        
        print(water)
        for loc in water:
            builder.add_object(loc,'water', EnvObject,is_traversable=True, is_movable=False, area_visualize_colour='#0008ff', visualize_shape='img', img_name="/images/pool_full.svg")
  


    add_drop_off_zones(builder, task_type)
    add_agents(builder, condition, task_type, name, folder)

    return builder

class CollectableBlock(EnvObject):
    '''
    Objects that can be collected by agents.
    '''
    def __init__(self, location, name, visualize_shape, img_name):
        super().__init__(location, name, is_traversable=True, is_movable=True,
                         visualize_shape=visualize_shape,img_name=img_name,
                         visualize_size=object_size, class_callable=CollectableBlock,
                         is_drop_zone=False, is_goal_block=False, is_collectable=True)

class ObstacleObject(EnvObject):
    '''
    Obstacles that can be removed by agents
    '''
    def __init__(self, location, name, visualize_shape, img_name):
        super().__init__(location, name, is_traversable=False, is_movable=True,
                         visualize_shape=visualize_shape,img_name=img_name,
                         visualize_size=1.25, class_callable=ObstacleObject,
                         is_drop_zone=False, is_goal_block=False, is_collectable=False)

class GhostBlock(EnvObject):
    '''
    Objects on the drop zone that cannot be carried by agents.
    '''
    def __init__(self, location, drop_zone_nr, name, visualize_shape, img_name):
        super().__init__(location, name, is_traversable=True, is_movable=False,
                         visualize_shape=visualize_shape, img_name=img_name,
                         visualize_size=object_size, class_callable=GhostBlock,
                         visualize_depth=110, drop_zone_nr=drop_zone_nr, visualize_opacity=0.5,
                         is_drop_zone=False, is_goal_block=True, is_collectable=False)

class CollectionGoal(WorldGoal):
    '''
    The goal for world which determines when the simulator should stop.
    '''
    def __init__(self, max_nr_ticks):
        super().__init__()
        self.max_nr_ticks = max_nr_ticks
        self.__drop_off= {}
        self.__drop_off_zone = {}
        self.__progress = 0
        self.__score = 0
    
    def score(self, grid_world):
        return self.__score

    def goal_reached(self, grid_world):
        if grid_world.current_nr_ticks >= self.max_nr_ticks:
            return True
        #return self.isVictimPlaced(grid_world)

    def isVictimPlaced(self, grid_world):
        '''
        @return true if all victims have been rescued
        '''
        # find all drop off locations, its tile ID's and goal victims
        if self.__drop_off =={}:
            self.__find_drop_off_locations(grid_world)
        # Go through each drop zone, and check if the victims are there on the right spot
        is_satisfied, progress = self.__check_completion(grid_world)
        # Progress in percentage
        self.__progress = progress / sum([len(goal_vics) for goal_vics in self.__drop_off.values()])

        return is_satisfied

    def progress(self, grid_world):
        # find all drop off locations, its tile ID's and goal blocks
        if self.__drop_off =={}:  
            self.__find_drop_off_locations(grid_world)
        # Go through each drop zone, and check if the victims are there in the right spot
        is_satisfied, progress = self.__check_completion(grid_world)
        # Progress in percentage
        self.__progress = progress / sum([len(goal_vics) for goal_vics in self.__drop_off.values()])
        return self.__progress

    def __find_drop_off_locations(self, grid_world):
        goal_vics = {} 
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():  # go through all objects
            if "drop_zone_nr" in obj.properties.keys():  # check if the object is part of a drop zone
                zone_nr = obj.properties["drop_zone_nr"]  # obtain the zone number
                if obj.properties["is_goal_block"]:  # check if the object is a ghostly goal victim
                    if zone_nr in goal_vics.keys():  # create or add to the list
                        goal_vics[zone_nr].append(obj)
                    else:
                        goal_vics[zone_nr] = [obj]

        self.__drop_off_zone = {}
        self.__drop_off = {}
        for zone_nr in goal_vics.keys():  # go through all drop of zones and fill the drop_off dict
            # Instantiate the zone's dict.
            self.__drop_off_zone[zone_nr] = {}
            self.__drop_off[zone_nr] = {}
            # Obtain the zone's goal victims.
            vics = goal_vics[zone_nr].copy()
            # The number of victims is the maximum number of victims to collect for this zone.
            max_rank = len(vics)
            # Find the 'bottom' location
            bottom_loc = (-np.inf, -np.inf)
            for vic in vics:
                if vic.location[1] > bottom_loc[1]:
                    bottom_loc = vic.location
            # Now loop through victim lists and add them to their appropriate ranks
            for rank in range(max_rank):
                loc = (bottom_loc[0], bottom_loc[1]-rank)
                # find the victim at that location
                for vic in vics:
                    if vic.location == loc:
                        # Add to self.drop_off
                        self.__drop_off_zone[zone_nr][rank] = [loc, vic.properties['img_name'][8:-4], None]
                        for i in self.__drop_off_zone.keys():
                            self.__drop_off[i] = {}
                            vals = list(self.__drop_off_zone[i].values())
                            vals.reverse()
                            for j in range(len(self.__drop_off_zone[i].keys())):
                                self.__drop_off[i][j] = vals[j]

    def __check_completion(self, grid_world):
        # Get the current tick number
        curr_tick = grid_world.current_nr_ticks
        # loop through all zones, check the victims and set the tick if satisfied
        for zone_nr, goal_vics in self.__drop_off.items():
            # Go through all ranks of this drop off zone
            for rank, vic_data in goal_vics.items():
                loc = vic_data[0]  # the location, needed to find victims here
                shape = vic_data[1]  # the desired shape
                tick = vic_data[2]

                # Retrieve all objects, the object ids at the location and obtain all victims from it
                all_objs = grid_world.environment_objects
                obj_ids = grid_world.get_objects_in_range(loc, object_type=EnvObject, sense_range=0)
                vics = [all_objs[obj_id] for obj_id in obj_ids
                          if obj_id in all_objs.keys() and "is_collectable" in all_objs[obj_id].properties.keys()]
                vics = [v for v in vics if v.properties["is_collectable"]]

                # Check if there is a victim, and if so if it is the right one and the tick is not yet set, then set the current tick and increase the score.
                if len(vics) > 0 and vics[0].properties['img_name'][8:-4] == shape and tick is None:
                    self.__drop_off[zone_nr][rank][2] = curr_tick
                    if 'critical' in vics[0].properties['img_name'][8:-4]:
                        self.__score+=6
                    if 'mild' in vics[0].properties['img_name'][8:-4]:
                        self.__score+=3
                # Deduct points from the score when victims are picked up from drop zone
                elif len(vics) == 0:
                    if self.__drop_off[zone_nr][rank][2] != None:
                        self.__drop_off[zone_nr][rank][2] = None
                        if rank in [0,1,2,3]:
                            self.__score-=6
                        if rank in [4,5,6,7]:
                            self.__score-=3

        # Now check if all victims are collected
        is_satisfied = True
        progress = 0
        for zone_nr, goal_vics in self.__drop_off.items():
            zone_satisfied = True
            ticks = [goal_vics[r][2] for r in range(len(goal_vics))]  # list of ticks in rank order
            for tick in ticks:
                if tick is not None:
                    progress += 1
            if None in ticks:
                zone_satisfied = False
            # update our satisfied boolean
            is_satisfied = is_satisfied and zone_satisfied
        agent = grid_world.registered_agents['rescuebot']
        agent.change_property('score',self.__score)

        return is_satisfied, progress