import os
import sys
import numpy as np
import pandas as pd
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
from agents1.MissionAgent import BaselineAgent
from agents1.TutorialAgent import TutorialAgent
from actions1.CustomActions import RemoveObjectTogether
from brains1.HumanBrain import HumanBrain
from loggers.ActionLogger import ActionLoggerV2
from datetime import datetime
import requests
import random
import csv
import table_api

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
        'w': Drop.__name__
    }

# Some settings
nr_areas = 8
wall_color = "#464646"
background_color = "#C2A9A1"
background_image = "./images/background.png"
pick_up_area_1_color = "#4b6473"
pick_up_area_2_color = "#EDC001"
drop_off_color = "#023020"
object_size = 0.9
victims_per_area_mission = 2
victims_per_area_tutorial = 1
nr_teams = 1
agents_per_team = 2
human_agents_per_team = 1
agent_sense_range = 2  # the range with which agents detect other agents. Do not change this value.
object_sense_range = 1  # the range with which agents detect blocks. Do not change this value.
other_sense_range = np.inf  # the range with which agents detect other objects (walls, doors, etc.). Do not change this value.
fov_occlusion = True
drop_width = 6
drop_height = 6

ALL_AREAS = ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2"]


#Choose Will Agent's areas based on human preferences (on file):
def pick_agent_areas(agent_type):
    df = pd.read_csv(table_api.PREFERENCES_CSV)

    if agent_type == "will":

        close_pref = df.loc[df["pref_id"] == "close", "preference_num"].values[0]
        far_pref = df.loc[df["pref_id"] == "far", "preference_num"].values[0]
        water_pref = df.loc[df["pref_id"] == "water", "preference_num"].values[0]
        dry_pref = df.loc[df["pref_id"] == "dry", "preference_num"].values[0]

        # Determine task allocation based on preferences
        if close_pref > far_pref:
            if dry_pref > water_pref:
                if close_pref >= dry_pref:
                    my_areas = ["A1", "B1", "C1", "D1"]
                else:
                    my_areas = ["A1", "A2", "D1", "D2"]
            elif water_pref > dry_pref:
                if close_pref >= water_pref:
                    my_areas = ["A1", "B1", "C1", "D1"]
                else:
                    my_areas = ["B1", "B2", "C1", "C2"]
            else:  # No soil preference
                my_areas = ["A1", "B1", "C1", "D1"]

        elif far_pref > close_pref:
            if dry_pref > water_pref:
                if far_pref >= dry_pref:
                    my_areas = ["A2", "B2", "C2", "D2"]
                else:
                    my_areas = ["A1", "A2", "D1", "D2"]
            elif water_pref > dry_pref:
                if far_pref >= water_pref:
                    my_areas = ["A2", "B2", "C2", "D2"]
                else:
                    my_areas = ["B1", "B2", "C1", "C2"]
            else:  # No soil preference
                my_areas = ["A2", "B2", "C2", "D2"]

        else:  # No distance preference
            my_areas = ["A1", "A2", "B1", "B2"]

        print("Selected tasks:", my_areas)
    
    else:
        my_areas = ["A1", "A2", "B1", "B2"]

    return my_areas


# Add the drop zones to the world
def add_drop_off_zones(builder, task_type):
    if task_type == "mission":
        nr_drop_zones = 1
        for nr_zone in range(nr_drop_zones):
            builder.add_area((16,9), width=3, height=2, name=f"Drop off {nr_zone}", visualize_opacity=0.3, visualize_colour=drop_off_color, drop_zone_nr=nr_zone, is_drop_zone=True, is_goal_block=False, is_collectable=False) 


# Add the agents to the world
def add_agents_simulation(builder, condition, task_type, name, folder, victims):

    for team in range(nr_teams):
        team_name = f"Team {team}"
        # Add the artificial agents based on condition
        nr_agents = agents_per_team - human_agents_per_team
        brain1 = BaselineAgent(slowdown=1, condition=condition, human_name=name,agent_name="RescueBot", my_areas=["C1","C2","D1","D2"], victim_order=victims, folder=folder) # Slowdown makes the agent a bit slower, do not change value during evaluations
        loc = (20,20)
        builder.add_agent(loc, brain1, team=team_name, name="RescueBot", visualize_size=2.0, is_traversable=True, img_name="/images/robot-final4.svg", score=0)

        brain2 = BaselineAgent(slowdown=1, condition=condition, human_name=name,agent_name="Helper", my_areas=["A1","A2","B1","B2"], victim_order=victims, folder=folder) # Slowdown makes the agent a bit slower, do not change value during evaluations
        loc = (21,21)
        builder.add_agent(loc, brain2, team=team_name, name="Helper", visualize_size=2.0, is_traversable=True, img_name="/images/robot-final4.svg", score=0)

        # Add human agents based on condition, do not change human brain values
        for human_agent_nr in range(human_agents_per_team):
            brain = HumanBrain(max_carry_objects=1, grab_range=1, drop_range=0, remove_range=1, fov_occlusion=fov_occlusion, strength=condition, name=name)
            loc = (18,22)
            builder.add_human_agent(location=loc, agent_brain=brain, team=team_name, name=name, visualize_size=2.0, key_action_map=key_action_map, is_traversable=True, img_name="/images/rescue-man-final3.svg", visualize_when_busy=True)


# Create the world for tutorial
def build_tutorial(name, participant_id, folder, victims_per_area, areas):
    goal = CollectionGoal(max_nr_ticks=np.inf)

    builder = WorldBuilder(shape=[40,40], tick_duration=tick_duration, run_matrx_api=True, run_matrx_visualizer=False, verbose=verbose, simulation_goal=goal,visualization_bg_img=background_image)

    build_areas_w_victims(builder, victims_per_area, areas)
    build_sar_env(builder)

    brain = HumanBrain(max_carry_objects=1, grab_range=1, drop_range=0, remove_range=1, fov_occlusion=fov_occlusion, name=name)
    loc = (18,22)
    builder.add_human_agent(location=loc, agent_brain=brain, team="Team", name=name, visualize_size=2.0, key_action_map=key_action_map, is_traversable=True, img_name="/images/rescue-man-final3.svg", visualize_when_busy=True)

    return builder


def build_mission(name, condition, participant_id, agent_type, folder, victims_per_area, areas):
    goal = CollectionGoal(max_nr_ticks=np.inf)

    builder = WorldBuilder(shape=[40,40], tick_duration=tick_duration, run_matrx_api=True, run_matrx_visualizer=False, verbose=verbose, simulation_goal=goal,visualization_bg_img=background_image)

    victims = build_areas_w_victims(builder, victims_per_area, areas)
    build_sar_env(builder)

    brain = HumanBrain(max_carry_objects=1, grab_range=1, drop_range=0, remove_range=1, fov_occlusion=fov_occlusion, name=name)
    loc = (18,22)
    builder.add_human_agent(location=loc, agent_brain=brain, team="Team", name=name, visualize_size=2.0, key_action_map=key_action_map, is_traversable=True, img_name="/images/rescue-man-final3.svg", visualize_when_busy=True)

    agent_areas = pick_agent_areas(agent_type)
    table_api.agent_areas = agent_areas

    # After assigning `my_areas` to the agent:
    table_api.human_areas = [area for area in ALL_AREAS if area not in agent_areas]

    if condition == "mission_comm": 
        brain1 = BaselineAgent(slowdown=1, condition=condition, agent_type=agent_type, human_name=name,agent_name="RescueBot", my_areas=agent_areas, victim_order=victims, folder=folder) # Slowdown makes the agent a bit slower, do not change value during evaluations
    elif condition == "mission_nocomm":
        brain1 = BaselineAgent(slowdown=1, condition=condition, agent_type=agent_type, human_name=name,agent_name="RescueBot", my_areas=agent_areas, victim_order=victims, folder=folder) # Slowdown makes the agent a bit slower, do not change value during evaluations
    loc = (20,20)
    builder.add_agent(loc, brain1, team="Team", name="RescueBot", visualize_size=2.0, is_traversable=True, img_name="/images/robot-final4.svg", score=0)


    return builder


def build_areas_w_victims(builder, victims_per_area, areas):
    n_areas = len(areas)
    n_victims = victims_per_area * n_areas
    victims = [{} for _ in range(n_victims)]
    order_victims = list(range(1,n_victims + 1))
    random.shuffle(order_victims)

    builder.add_room(top_left_location=(0, 0), width=40, height=40, name="world_bounds", wall_visualize_colour=None)

    v1 = 0

    # Add the areas and victims to each area
    for area_name, area_data in areas.items():
        builder.add_area(area_data["top_left"], width=area_data["width"], height=area_data["height"], name=area_name, visualize_opacity=0.5, visualize_colour=area_data["color"], is_drop_zone=False, is_goal_block=False, is_collectable=False)

        # Pick x and y locations for victims in an area
        loc_victim_x = random.sample(range(area_data["top_left"][0], area_data["top_left"][0] + area_data["width"]), victims_per_area)
        loc_victim_y = random.sample(range(area_data["top_left"][1], area_data["top_left"][1] + area_data["height"]), victims_per_area)


        for v2 in range(victims_per_area):
            victim = order_victims[v1]
            #print(victim)
            drop_x = 17 + ((victim-1) % drop_width)
            drop_y = 17 + ((victim-1) // drop_width)
            #print(drop_x, drop_y)
            victims[victim - 1] = {"location": (loc_victim_x[v2],loc_victim_y[v2]), "name": "victim_"+str(victim)+"_", "area": area_name, "order": victim, "drop_location": (drop_x, drop_y)}
            builder.add_object(location=(loc_victim_x[v2],loc_victim_y[v2]),name="victim_"+str(victim)+"_", callable_class=CollectableBlock, visualize_shape='img',img_name="/images/victims/v"+str(victim)+".svg")

            builder.add_object((drop_x,drop_y), "drop_off_"+str(victim)+"_", callable_class=GhostBlock, visualize_shape='img',img_name="/images/victims/v"+str(victim)+".svg", drop_zone_nr=1)
            
            v1 += 1

    return victims

def build_sar_env(builder):

        # Add the drop off zones

        builder.add_area((17,17), width=drop_width, height=drop_height, name="Drop off", visualize_opacity=0.5, visualize_colour=drop_off_color, drop_zone_nr=1, is_drop_zone=True, is_goal_block=False, is_collectable=False) 

        # Add decorative objects
        builder.add_object((23,15),'heli',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/helicopter.svg", visualize_size=4) 
        builder.add_object((15,23),'ambulance',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/ambulance.svg", visualize_size=3) 

    # Create folders where the logs are stored during the official condition
        # current_exp_folder = datetime.now().strftime("exp_"+condition+"_at_time_%Hh-%Mm-%Ss_date_%dd-%mm-%Yy")
        # logger_save_folder = os.path.join("logs", current_exp_folder)
        # builder.add_logger(ActionLoggerV2, log_strategy=1, save_path=logger_save_folder, file_name_prefix="actions_")
        
    # Add water area
        water = [(x, y) for x in range(29, 40) for y in range(6, 14)] + [(x, y) for x in range(27, 40) for y in range(14, 21)] + \
                [(x, y) for x in range(24, 40) for y in range(21, 23)] + [(x, y) for x in range(21, 40) for y in range(23, 25)] + \
                [(x, y) for x in range(16, 40) for y in range(25, 27)] + [(x, y) for x in range(14, 40) for y in range(27, 30)] + \
                [(x, y) for x in range(10, 40) for y in range(30, 35)] + [(x, y) for x in range(8, 40) for y in range(35, 40)]    
                # [(x,y) for x in list(range(2,6)) for y in list(range(15,18))] + [(x,y) for x in list(range(14,18)) for y in list(range(15,18))] + \
                # [(6,16),(6,17),(13,16),(13,17)] + + [(x,13) for x in list(range(2,4))] + [(x,13) for x in list(range(16,18))]
        
        #print(water)
        for loc in water:
            builder.add_object(loc,'water', EnvObject,is_traversable=True, is_movable=False, area_visualize_colour='#0008ff', visualize_opacity=0)



# Create the world
def create_builder(condition, agent_type, name, participant_id, folder):
    random.seed(random_seed)
    # Set numpy's random generator
    np.random.seed(random_seed)

    table_api.PREFERENCES_CSV = folder + "/preferences.csv"

    areas = {"A1": {"top_left": (14,8), "width": 12, "height": 5, "color": pick_up_area_1_color}, "A2": {"top_left": (14,2), "width": 12, "height": 5, "color": pick_up_area_2_color},
                "B1": {"top_left": (27,14), "width": 5, "height": 12, "color": pick_up_area_1_color}, "B2": {"top_left": (33,14), "width": 5, "height": 12, "color": pick_up_area_2_color},
                "C1": {"top_left": (14,27), "width": 12, "height": 5, "color": pick_up_area_1_color}, "C2": {"top_left": (14,33), "width": 12, "height": 5, "color": pick_up_area_2_color},
                "D1": {"top_left": (8,14), "width": 5, "height": 12, "color": pick_up_area_1_color}, "D2": {"top_left": (2,14), "width": 5, "height": 12, "color": pick_up_area_2_color}}

    if condition== "tutorial":
        with open(table_api.PREFERENCES_CSV, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["pref_id", "preference", "preference_num"])
        
        builder = build_tutorial(name, participant_id, folder, victims_per_area_tutorial, areas)

    # Create the world builder
    if condition=="mission_nocomm" or condition=="mission_comm":
        builder = build_mission(name=name, condition=condition, participant_id=participant_id, agent_type=agent_type, folder=folder, victims_per_area=victims_per_area_mission, areas=areas)


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
        self.__all_vics = []
        self.__goal_vics = []
        self.__progress = 0
        self.__score = 0
    
    def score(self, grid_world):
        return self.__score

    def goal_reached(self, grid_world):
        if grid_world.current_nr_ticks >= self.max_nr_ticks:
            return True
        return self.allVictimsPlaced(grid_world)

    def allVictimsPlaced(self, grid_world):
        '''
        @return true if all victims have been rescued
        '''
        # find all drop off locations, its tile ID's and goal victims
        if self.__goal_vics == []:
            self.__find_drop_off_locations(grid_world)
        # Go through each drop zone, and check if the victims are there on the right spot
        is_satisfied, progress = self.__check_completion(grid_world)
        # Progress in percentage
        self.__progress = progress / len(self.__goal_vics)
        #print("goal vics", self.__drop_off.values())

        #print("Progress", self.__progress, "is_satisfied", is_satisfied)
        return is_satisfied

    def __find_drop_off_locations(self, grid_world):
        goal_vics = [] 
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():  # go through all objects
            if "drop_zone_nr" in obj.properties.keys():  # check if the object is part of a drop zone
                if obj.properties["is_goal_block"]:
                    # check if the object is a ghostly goal victim
                    #print("obj",obj.properties)
                    goal_vics += [obj.properties]
        self.__goal_vics = goal_vics

    def __update_victims(self, grid_world):
        vics = [] 
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():  # go through all objects
            if "is_collectable" in obj.properties.keys() and obj.properties["is_collectable"]:
                # check if the object is a ghostly goal victim
                #print("obj",obj.properties)
                vics += [obj.properties]

        self.__all_vics = vics

    def __check_completion(self, grid_world):
        # Get the current tick number
        curr_tick = grid_world.current_nr_ticks
        coll_count = 0
        # loop through all zones, check the victims and set the tick if satisfied
        #print("goal vics", self._goal_vics)
        self.__update_victims(grid_world)
        for v in self.__goal_vics:
            #print("Here", v['name'])
            length = len(v['name'])
            drop_order = v['name'][9:length-1]
            #print(drop_order, self._last_vic, self._goal_vic['order'])
            vic_name = "victim_" + drop_order + "_"
            for v2 in self.__all_vics:
                #print("names", v2['name'], vic_name)
                if v2['name'] == vic_name:
                    #print("location", v2['location'], v['location'])
                    if v2['location'] == v['location']:
                        coll_count += 1
                        break

        # Now check if all victims are collected
        if coll_count == len(self.__goal_vics):
            is_satisfied = True
        else:
            is_satisfied = False
        
        progress = coll_count

        return is_satisfied, progress
    

def trigger_table():
    generate_table_html()
    generate_table_json()

    try:
        requests.get('http://localhost:5001/trigger_communication')
    except Exception as e:
        print(f"Failed to send communication trigger: {e}")

def generate_table_html():
    # make interactive table with listed tasks
    return

def generate_table_json():
    return