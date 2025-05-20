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
background_image = "./images/background_20x20.png"
pick_up_area_1_color = "#4b6473"
pick_up_area_2_color = "#EDC001"
drop_off_color = "#CEDDBB"
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
drop_width = 4
drop_height = 4

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


def add_drop_off_zones(builder, task_type):
    if task_type == "mission":
        nr_drop_zones = 1
        for nr_zone in range(nr_drop_zones):
            builder.add_area((8,4), width=2, height=2, name=f"Drop off {nr_zone}", visualize_opacity=0.3, visualize_colour=drop_off_color, drop_zone_nr=nr_zone, is_drop_zone=True, is_goal_block=False, is_collectable=False)

def add_agents_simulation(builder, condition, task_type, name, folder, victims):
    for team in range(nr_teams):
        team_name = f"Team {team}"
        nr_agents = agents_per_team - human_agents_per_team

        brain1 = BaselineAgent(slowdown=1, condition=condition, human_name=name,agent_name="RescueBot", my_areas=["C1","C2","D1","D2"], victim_order=victims, folder=folder)
        builder.add_agent((10,10), brain1, team=team_name, name="RescueBot", visualize_size=1.0, is_traversable=True, img_name="/images/robot-final4.svg", score=0)

        brain2 = BaselineAgent(slowdown=1, condition=condition, human_name=name,agent_name="Helper", my_areas=["A1","A2","B1","B2"], victim_order=victims, folder=folder)
        builder.add_agent((10,11), brain2, team=team_name, name="Helper", visualize_size=1.0, is_traversable=True, img_name="/images/robot-final4.svg", score=0)

def build_tutorial(name, participant_id, folder, victims_per_area, areas):
    goal = CollectionGoal(max_nr_ticks=np.inf)

    builder = WorldBuilder(shape=[20,20], tick_duration=tick_duration, run_matrx_api=True, run_matrx_visualizer=False, verbose=verbose, simulation_goal=goal,visualization_bg_img=background_image)

    build_areas_w_victims(builder, victims_per_area, areas)
    build_sar_env(builder)

    brain = HumanBrain(max_carry_objects=1, grab_range=0, drop_range=0, remove_range=1, fov_occlusion=fov_occlusion, condition="tutorial", name=name)
    builder.add_human_agent(location=(7,7), agent_brain=brain, team="Team", name=name, visualize_size=1.0, key_action_map=key_action_map, is_traversable=True, img_name="/images/rescue-man-final3.svg", visualize_when_busy=True)

    return builder

def build_mission(name, condition, participant_id, agent_type, agent_name, folder, victims_per_area, areas):
    goal = CollectionGoal(max_nr_ticks=np.inf)

    builder = WorldBuilder(shape=[20,20], tick_duration=tick_duration, run_matrx_api=True, run_matrx_visualizer=False, verbose=verbose, simulation_goal=goal,visualization_bg_img=background_image)

    victims = build_areas_w_victims(builder, victims_per_area, areas)
    build_sar_env(builder)

    agent_areas = pick_agent_areas(agent_type)
    table_api.agent_areas = agent_areas
    table_api.human_areas = [area for area in ALL_AREAS if area not in agent_areas]

    brain = HumanBrain(max_carry_objects=1, grab_range=0, drop_range=0, remove_range=1, fov_occlusion=fov_occlusion, condition=condition, name=name, victim_order=victims, participant_id=participant_id, agent_name = agent_name,my_areas=table_api.human_areas)
    builder.add_human_agent(location=(7,8), agent_brain=brain, participant_id=participant_id, team="Team", name=name, visualize_size=1.0, key_action_map=key_action_map, is_traversable=True, img_name="/images/rescue-man-final3.svg", visualize_when_busy=True)

    brain1 = BaselineAgent(slowdown=1, condition=condition, participant_id=participant_id, agent_type=agent_type, human_name=name,agent_name=agent_name, my_areas=agent_areas, victim_order=victims, folder=folder)
    builder.add_agent((7,9), brain1, team="Team", name=agent_name, visualize_size=1.0, is_traversable=True, img_name="/images/" + agent_name + ".svg", score=0)

    return builder

def build_areas_w_victims(builder, victims_per_area, areas):
    n_areas = len(areas)
    n_victims = victims_per_area * n_areas
    victims = [{} for _ in range(n_victims)]
    order_victims = list(range(1,n_victims + 1))
    random.shuffle(order_victims)

    builder.add_room(top_left_location=(0, 0), width=20, height=20, name="world_bounds", wall_visualize_colour=None)

    v1 = 0

    for area_name, area_data in areas.items():
        top_left = (area_data["top_left"][0], area_data["top_left"][1])
        width = area_data["width"]
        height = area_data["height"]
        builder.add_area(top_left, width=width, height=height, name=area_name, visualize_opacity=0.5, visualize_colour=area_data["color"], is_drop_zone=False, is_goal_block=False, is_collectable=False)

        loc_victim_x = random.sample(range(top_left[0], top_left[0] + width), victims_per_area)
        loc_victim_y = random.sample(range(top_left[1], top_left[1] + height), victims_per_area)

        for v2 in range(victims_per_area):
            victim = order_victims[v1]
            drop_x = 8 + ((victim-1) % (drop_width))
            drop_y = 8 + ((victim-1) // (drop_height))
            victims[victim - 1] = {"location": (loc_victim_x[v2], loc_victim_y[v2]), "name": "victim_"+str(victim)+"_", "area": area_name, "order": victim, "drop_location": (drop_x, drop_y)}
            builder.add_object((loc_victim_x[v2], loc_victim_y[v2]),"victim_"+str(victim)+"_", callable_class=CollectableBlock, visualize_shape='img',img_name="/images/victims/v"+str(victim)+".png")
            builder.add_object((drop_x, drop_y), "drop_off_"+str(victim)+"_", callable_class=GhostBlock, visualize_shape='img',img_name="/images/victims/v"+str(victim)+".png", drop_zone_nr=1)
            v1 += 1

    return victims

def build_sar_env(builder):
    builder.add_area((8,8), width=drop_width, height=drop_height, name="Drop off", visualize_opacity=0.0, visualize_colour=drop_off_color, drop_zone_nr=1, is_drop_zone=True, is_goal_block=False, is_collectable=False)

    builder.add_object((14,2),'heli',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/helicopter.svg", visualize_size=2)
    builder.add_object((6,11),'ambulance',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/ambulance.svg", visualize_size=2)

    water = [(4, 17), (4, 18), (4, 19), 
             (5, 15), (5, 16), (5, 17), (5, 18), (5, 19), 
             (6, 15), (6, 16), (6, 17), (6, 18), (6, 19), 
             (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), 
             (8, 13), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19), 
             (9, 13), (9, 14), (9, 15), (9, 16), (9, 17), (9, 18), (9, 19), 
             (10, 13), (10, 14), (10, 15), (10, 16), (10, 17), (10, 18), (10, 19), 
             (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19), 
              (12, 12), (12, 13), (12, 14), (12, 15), (12, 16), (12, 17), (12, 18), (12, 19), 
             (13, 7), (13, 8), (13, 9), (13, 10), (13, 11), (13, 12), (13, 13), (13, 14), (13, 15), (13, 16), (13, 17), (13, 18), (13, 19), 
             (14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9), (14, 10), (14, 11), (14, 12), (14, 13), (14, 14), (14, 15), (14, 16), (14, 17), (14, 18), (14, 19), 
             (15, 3), (15, 4), (15, 5), (15, 6), (15, 7), (15, 8), (15, 9), (15, 10), (15, 11), (15, 12), (15, 13), (15, 14), (15, 15), (15, 16), (15, 17), (15, 18), (15, 19), 
             (16, 3), (16, 4), (16, 5), (16, 6), (16, 7), (16, 8), (16, 9), (16, 10), (16, 11), (16, 12), (16, 13), (16, 14), (16, 15), (16, 16), (16, 17), (16, 18), (16, 19), 
             (17, 3), (17, 4), (17, 5), (17, 6), (17, 7), (17, 8), (17, 9), (17, 10), (17, 11), (17, 12), (17, 13), (17, 14), (17, 15), (17, 16), (17, 17), (17, 18), (17, 19), 
             (18, 3), (18, 4), (18, 5), (18, 6), (18, 7), (18, 8), (18, 9), (18, 10), (18, 11), (18, 12), (18, 13), (18, 14), (18, 15), (18, 16), (18, 17), (18, 18), (18, 19), 
             (19, 3), (19, 4), (19, 5), (19, 6), (19, 7), (19, 8), (19, 9), (19, 10), (19, 11), (19, 12), (19, 13), (19, 14), (19, 15), (19, 16), (19, 17), (19, 18), (19, 19)]


    for loc in water:
        builder.add_object(loc,'water', EnvObject,is_traversable=True, is_movable=False, area_visualize_colour='#0008ff', visualize_opacity=0)

def create_builder(condition, agent_type, name, participant_id, agent_name, folder):
    random.seed(random_seed)
    np.random.seed(random_seed)

    areas = {
        "A1": {"top_left": (7, 3), "width": 6, "height": 2, "color": pick_up_area_1_color},
        "A2": {"top_left": (7, 1), "width": 6, "height": 2, "color": pick_up_area_2_color},
        "B1": {"top_left": (15, 7), "width": 2, "height": 6, "color": pick_up_area_1_color},
        "B2": {"top_left": (17, 7), "width": 2, "height": 6, "color": pick_up_area_2_color},
        "C1": {"top_left": (7, 15), "width": 6, "height": 2, "color": pick_up_area_1_color},
        "C2": {"top_left": (7, 17), "width": 6, "height": 2, "color": pick_up_area_2_color},
        "D1": {"top_left": (3, 7), "width": 2, "height": 6, "color": pick_up_area_1_color},
        "D2": {"top_left": (1, 7), "width": 2, "height": 6, "color": pick_up_area_2_color}
    }

    if condition == "tutorial":
        with open(table_api.PREFERENCES_CSV, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["pref_id", "preference", "preference_num"])
        
        builder = build_tutorial(name, participant_id, folder, victims_per_area_tutorial, areas)

    elif condition in ["mission_comm", "mission_nocomm"]:
        builder = build_mission(
            name=name,
            condition=condition,
            participant_id=participant_id,
            agent_type=agent_type,
            agent_name = agent_name,
            folder=folder,
            victims_per_area=victims_per_area_mission,
            areas=areas
        )

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
        # Update internal victim tracking
        self.__update_victims(grid_world)


        # Completion: all goal victims have been dropped correctly
        coll_count = table_api.human_vics_saved_abs + table_api.agent_vics_saved_abs + table_api.agent_vics_saved_by_human_abs
        is_satisfied = (coll_count == len(self.__goal_vics))
        progress = coll_count / len(self.__goal_vics)
        #print(coll_count,progress,len(self.__goal_vics))

        table_api.completeness = progress

        return is_satisfied, progress
