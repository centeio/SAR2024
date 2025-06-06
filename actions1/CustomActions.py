import numpy as np
from matrx.actions.action import Action, ActionResult
from matrx.objects.agent_body import AgentBody
from matrx.objects.standard_objects import AreaTile
from matrx.actions.object_actions import _is_drop_poss, _act_drop, _possible_drop, _find_drop_loc, GrabObject, GrabObjectResult, RemoveObject, RemoveObjectResult, DropObject
from matrx.utils import get_distance
import random

class Idle(Action):
    """ Let's an agent be idle for a specified number of ticks.
    Parameters
    ----------
    action_duration : int
        Optional. Default: ``1``. Should be zero or larger.
        The default duration of this action in ticks during which the
        :class:`matrx.grid_world.GridWorld` blocks the agent performing other
        actions. By default this is 1, meaning that all actions of this type will take
        both the tick in which it was decided upon and the subsequent tick.
        When the agent is blocked / busy with an action, only the
        :meth:`matrx.agents.agent_brain.AgentBrain.filter_observations` method is called for that agent, and the
        :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method is skipped.
        This means that agents that are busy with an action can only perceive the world but not decide on
        a new action untill the action has completed.
        An agent can overwrite the duration of an action by returning the ``action_duration`` in the ``action_kwargs``
        in the :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method, as so:
        ``return >action_name<, {'action_duration': >ticks<}``
    """
    def __init__(self, action_duration=1):
        super().__init__(action_duration)

    def is_possible(self, grid_world, agent_id, **kwargs):
        return IdleResult(IdleResult.RESULT_SUCCESS, True)


class IdleResult(ActionResult):
    RESULT_SUCCESS = 'Idling action successful'
    RESULT_FAILED = 'Failed to idle'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)

class RemoveObjectTogether(Action):
    """ Removes an object from the world.
    An action that permanently removes an
    :class:`matrx.objects.env_object.EnvObject` from the world, which can be
    any object except for the agent performing the action.
    Parameters
    ----------
    action_duration : int
        Optional. Default: ``1``. Should be zero or larger.
        The default duration of this action in ticks during which the
        :class:`matrx.grid_world.GridWorld` blocks the agent performing other
        actions. By default this is 1, meaning that all actions of this type will take
        both the tick in which it was decided upon and the subsequent tick.
        When the agent is blocked / busy with an action, only the
        :meth:`matrx.agents.agent_brain.AgentBrain.filter_observations` method is called for that agent, and the
        :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method is skipped.
        This means that agents that are busy with an action can only perceive the world but not decide on
        a new action untill the action has completed.
        An agent can overwrite the duration of an action by returning the ``action_duration`` in the ``action_kwargs``
        in the :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method, as so:
        ``return >action_name<, {'action_duration': >ticks<}``
    """

    def __init__(self, action_duration=0):
        super().__init__(action_duration)

    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        """ Removes the specified object.
        Removes a specific :class:`matrx.objects.env_object.EnvObject` from
        the world. Can be any object except for the agent performing the
        action.
        Parameters
        ----------
        grid_world : GridWorld
            The ``matrx.grid_world.GridWorld`` instance in which the object is
            sought according to the `object_id` parameter.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when performing an
            action. Note that this is the State of the entire world, not
            that of the agent performing the action.
        object_id: str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            removed. If not given, the closest object is selected.
            removed.
        remove_range : int (Optional. Default: 1)
            The range in which the :class:`matrx.objects.env_object.EnvObject`
            should be in for it to be removed.
        Returns
        -------
        RemoveObjectResult
            Depicts the action's success or failure and reason for that result.
            See :class:`matrx.actions.object_actions.RemoveObjectResult` for
            the results it can contain.
        """
        assert 'object_id' in kwargs.keys()  # assert if object_id is given.
        object_id = kwargs['object_id']  # assign
        remove_range = 1  # default remove range
        other_agent = world_state[{"name": "RescueBot"}]
        other_human = world_state[{"name": kwargs['human_name']}]
        if 'remove_range' in kwargs.keys():  # if remove range is present
            assert isinstance(kwargs['remove_range'], int)  # should be of integer
            assert kwargs['remove_range'] >= 0  # should be equal or larger than 0
            remove_range = kwargs['remove_range']  # assign

        # get the current agent (exists, otherwise the is_possible failed)
        agent_avatar = grid_world.registered_agents[agent_id]
        agent_loc = agent_avatar.location  # current location

        # Get all objects in the remove_range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_id)

        for obj in objects_in_range:  # loop through all objects in range
            if obj == object_id and get_distance(other_agent['location'], world_state[obj]['location'])<=remove_range and get_distance(other_human['location'], world_state[obj]['location'])<=remove_range and 'rock' in obj or \
            obj == object_id and get_distance(other_agent['location'], world_state[obj]['location'])<=remove_range and get_distance(other_human['location'], world_state[obj]['location'])<=remove_range and 'stone' in obj:  # if object is in that list
                success = grid_world.remove_from_grid(object_id)  # remove it, success is whether GridWorld succeeded
                if success:  # if we succeeded in removal return the appropriate ActionResult
                    return RemoveObjectResult(RemoveObjectResult.OBJECT_REMOVED.replace('object_id'.upper(),
                                                                                        str(object_id)), True)
                else:  # else we return a failure due to the GridWorld removal failed
                    return RemoveObjectResult(RemoveObjectResult.REMOVAL_FAILED.replace('object_id'.upper(),
                                                                                        str(object_id)), False)

        # If the object was not in range, or no objects were in range we return that the object id was not in range
        return RemoveObjectResult(RemoveObjectResult.OBJECT_ID_NOT_WITHIN_RANGE
                                  .replace('remove_range'.upper(), str(remove_range))
                                  .replace('object_id'.upper(), str(object_id)), False)

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if an object can be removed.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            object is sought according to the `object_id` parameter.
        agent_id: str
            The string representing the unique identified that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when checking if an
            action can be performed. Note that this is the State of the
            entire world, not that of the agent performing the action.
        object_id: str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            removed. If not given, the closest object is selected.
        remove_range : int (Optional. Default: 1)
            The range in which the :class:`matrx.objects.env_object.EnvObject`
            should be in for it to be removed.
        Returns
        -------
        RemoveObjectResult
            The :class:`matrx.actions.action.ActionResult` depicting the
            action's expected success or failure and reason for that result.
            See :class:`matrx.actions.object_actions.RemoveObjectResult` for
            the results it can contain.
        """
        agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)  # get ourselves
        assert agent_avatar is not None  # check if we actually exist
        agent_loc = agent_avatar.location  # get our location

        remove_range = np.inf  # we do not know the intended range, so assume infinite
        # get all objects within infinite range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_avatar.obj_id)

        if len(objects_in_range) == 0:  # if there are no objects in infinite range besides ourselves, we return fail
            return RemoveObjectResult(RemoveObjectResult.NO_OBJECTS_IN_RANGE.replace('remove_range'.upper(),
                                                                                     str(remove_range)), False)
        # need an object id to remove an object
        if 'object_id' not in kwargs:
            return RemoveObjectResult(RemoveObjectResult.REMOVAL_FAILED.replace('object_id'.upper(),
                                                                                str(None)), False)
        # check if the object is actually within removal range
        object_id = kwargs['object_id']
        if object_id not in objects_in_range:
            return RemoveObjectResult(RemoveObjectResult.REMOVAL_FAILED.replace('object_id'.upper(),
                                                                                str(object_id)), False)

        # otherwise some instance of RemoveObject is possible, although we do not know yet IF the intended removal is
        # possible.
        return RemoveObjectResult(RemoveObjectResult.ACTION_SUCCEEDED, True)


class RemoveObjectResult(ActionResult):
    """ActionResult for a RemoveObjectAction
    The results uniquely for RemoveObjectAction are (as class constants):
    * OBJECT_REMOVED: If the object was successfully removed.
    * REMOVAL_FAILED: If the object could not be removed by the
      :class:`matrx.grid_world.GridWorld`.
    * OBJECT_ID_NOT_WITHIN_RANGE: If the object is not within specified range.
    * NO_OBJECTS_IN_RANGE: If no objects are within range.
    Parameters
    ----------
    result: str
        A string representing the reason for the (expected) success or fail of
        a :class:`matrx.actions.object_actions.RemoveObjectAction`.
    succeeded: bool
        A boolean representing the (expected) success or fail of a
        :class:`matrx.actions.object_actions.RemoveObjectAction`.
    See Also
    --------
    :class:`matrx.actions.object_actions.RemoveObjectAction`
    """

    """ Result when the specified object is successfully removed. """
    OBJECT_REMOVED = "The object with id `OBJECT_ID` is removed."

    """ Result when no objects were within the specified range. """
    NO_OBJECTS_IN_RANGE = "No objects were in `REMOVE_RANGE`."

    """ Result when the specified object is not within the specified range. """
    OBJECT_ID_NOT_WITHIN_RANGE = "The object with id `OBJECT_ID` is not within the range of `REMOVE_RANGE`."

    """ Result when the world could not remove the object for some reason. """
    REMOVAL_FAILED = "The object with id `OBJECT_ID` failed to be removed by the environment for some reason."

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class CarryObject(Action):
    """ Grab and hold objects.
    The action that can pick up / grab and hold an
    :class:`matrx.objects.env_object.EnvObject`. Cannot be performed on agents
    (including the agent performing the action). After grabbing / picking up,
    the object is automatically added to the agent's inventory and removed from
    the :class:`matrx.grid_world.GridWorld`.
    Parameters
    ----------
    action_duration : int
        Optional, default: ``1``. Should be zero or larger.
        The default duration of this action in ticks during which the
        :class:`matrx.grid_world.GridWorld` blocks the agent performing other
        actions. By default this is 1, meaning that all actions of this type will take
        both the tick in which it was decided upon and the subsequent tick.
        When the agent is blocked / busy with an action, only the
        :meth:`matrx.agents.agent_brain.AgentBrain.filter_observations` method is called for that agent, and the
        :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method is skipped.
        This means that agents that are busy with an action can only perceive the world but not decide on
        a new action untill the action has completed.
        An agent can overwrite the duration of an action by returning the ``action_duration`` in the ``action_kwargs``
        in the :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method, as so:
        ``return >action_name<, {'action_duration': >ticks<}``
    Notes
    -----
    The actual carrying mechanism of objects is implemented in the
    :class:`matrx.actions.move_actions.Move` actions: whenever an agent moves
    who holds objects, those objects it is holding are also moved with it.
    """

    def __init__(self, action_duration=0):
        super().__init__(action_duration)

    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        """ Checks if the object can be grabbed.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            object is sought according to the `object_id` parameter.
        agent_id: str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when checking if an
            action can be performed. Note that this is the State of the
            entire world, not that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            grabbed. When not given, a random object within range is selected.
        grab_range : int (Optional. Default: np.inf)
            The range in which the :class:`matrx.objects.env_object.EnvObject`
            should be in to be grabbed.
        max_objects : int (Optional. Default: np.inf)
            The maximum of objects the agent can carry.
        Returns
        -------
        GrabObjectResult
            Depicts the action's expected success or failure and reason for
            that result.
            See :class:`matrx.actions.object_actions.GrabObjectResult` for
            the results it can contain.
        """
        # Set default values check
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        grab_range = np.inf if 'grab_range' not in kwargs else kwargs['grab_range']
        max_objects = np.inf if 'max_objects' not in kwargs else kwargs['max_objects']
        if object_id and 'critical' in object_id:
            return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_UNMOVABLE, False)
        if object_id and 'stone' in object_id or object_id and 'rock' in object_id or object_id and 'tree' in object_id:
            return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_UNMOVABLE, False)
        else:
            return _is_possible_grab(grid_world, agent_id=agent_id, object_id=object_id, grab_range=grab_range,
                                    max_objects=max_objects) 

    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        """ Grabs an object.
        Alters the properties of the agent doing the grabbing, and the object
        being grabbed (and carried), such that the agent's inventory contains
        the entire object and the object being carried properties contains the
        agent's id.
        The grabbed object is removed from the world, and will only exist
        inside of the agent's inventory.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            object is sought according to the `object_id` parameter.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when performing an
            action. Note that this is the State of the entire world, not
            that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            grabbed. When not given, a random object within range is selected.
        grab_range : int (Optional. Default: np.inf)
            The range in which the :class:`matrx.objects.env_object.EnvObject`
            should be in to be grabbed.
        max_objects : int (Optional. Default: np.inf)
            The maximum of objects the agent can carry.
        Returns
        -------
        GrabObjectResult
            Depicts the action's expected success or failure and reason for
            that result.
            See :class:`matrx.actions.object_actions.GrabObjectResult` for
            the results it can contain.
        Notes
        -----
        A grabbed object resides inside the inventory of an agent, not directly
        in the world any longer. Hence, if the agent is removed, so is its
        inventory and all objects herein.
        """

        # Additional check
        assert 'object_id' in kwargs.keys()
        assert 'grab_range' in kwargs.keys()
        assert 'max_objects' in kwargs.keys()

        # if possible:
        object_id = kwargs['object_id']  # assign

        # Loading properties
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        env_obj = grid_world.environment_objects[object_id]  # Environment object

        # Updating properties
        env_obj.carried_by.append(agent_id)
        reg_ag.is_carrying.append(env_obj)  # we add the entire object!

        if 'healthy' in object_id and kwargs['human_name'] in agent_id:
            reg_ag.change_property("img_name", "/images/carry-healthy-human.svg")

        if 'mild' in object_id and kwargs['human_name'] in agent_id:
            reg_ag.change_property("img_name", "/images/carry-mild-human.svg")
        #if 'critical' in object_id and 'bot' in agent_id:
            # change our image 
        #    reg_ag.change_property("img_name", "/images/carry-critical-robot.svg")
        if 'mild' in object_id and 'bot' in agent_id:
            reg_ag.change_property("img_name", "/images/carry-mild-robot.svg")

        # Remove it from the grid world (it is now stored in the is_carrying list of the AgentAvatar
        succeeded = grid_world.remove_from_grid(object_id=env_obj.obj_id, remove_from_carrier=False)
        if not succeeded:
            return GrabObjectResult(GrabObjectResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD.replace("{OBJECT_ID}",
                                                                                                env_obj.obj_id), False)

        # Updating Location (done after removing from grid, or the grid will search the object on the wrong location)
        env_obj.location = reg_ag.location

        return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, True)


class GrabObjectResult(ActionResult):
    """ActionResult for a GrabObjectAction
    The results uniquely for GrabObjectAction are (as class constants):
    * RESULT_SUCCESS: When the object can be successfully grabbed.
    * RESULT_NO_OBJECT: When `object_id` is not given.
    * RESULT_CARRIES_OBJECT: When the agent already carries the maximum nr.
      objects.
    * NOT_IN_RANGE: When `object_id` not within range.
    * RESULT_AGENT: If the `object_id` is that of an agent.
    * RESULT_OBJECT_CARRIED: When the object is already carried by another
      agent.
    * RESULT_OBJECT_UNMOVABLE: When the object is not movable.
    * RESULT_UNKNOWN_OBJECT_TYPE: When the `object_id` does not exists in the
      :class:`matrx.grid_world.GridWorld`.
    * FAILED_TO_REMOVE_OBJECT_FROM_WORLD: When the grabbed object cannot be
      removed from the :class:`matrx.grid_world.GridWorld`.
    Parameters
    ----------
    result : str
        A string representing the reason for a
        :class:`matrx.actions.object_actions.GrabObjectAction` (expected)
        success or fail.
    succeeded : bool
        A boolean representing the (expected) success or fail of a
        :class:`matrx.actions.object_actions.GrabObjectAction`.
    See Also
    --------
    GrabObjectAction
    """

    """ Result when the object can be successfully grabbed. """
    RESULT_SUCCESS = 'Grab action success'

    """ Result when the grabbed object cannot be removed from the 
    :class:`matrx.grid_world.GridWorld`. """
    FAILED_TO_REMOVE_OBJECT_FROM_WORLD = 'Grab action failed; could not remove object with id {OBJECT_ID} from grid.'

    """ Result when the specified object is not within range. """
    NOT_IN_RANGE = 'Object not in range'

    """ Result when the specified object is an agent. """
    RESULT_AGENT = 'This is an agent, cannot be picked up'

    """ Result when no object was specified. """
    RESULT_NO_OBJECT = 'No Object specified'

    """ Result when the agent is at its maximum carrying capacity. """
    RESULT_CARRIES_OBJECT = 'Agent already carries the maximum amount of objects'

    """ Result when the specified object is already carried by another agent. 
    """
    RESULT_OBJECT_CARRIED = 'Object is already carried by {AGENT_ID}'

    """ Result when the specified object does not exist in the 
    :class:`matrx.grid_world.GridWorld` """
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'

    """ Result when the specified object is not movable. """
    RESULT_OBJECT_UNMOVABLE = 'Object is not movable'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)

class Drop(Action):
    """ Drops a carried object.
        The action that can drop an :class:`matrx.objects.env_object.EnvObject`
        that is in an agent's inventory. After dropping, the object is added to the
        :class:`matrx.grid_world.GridWorld`.
        Parameters
        ----------
        action_duration : int
            Optional, default: ``1``. Should be zero or larger.
            The default duration of this action in ticks during which the
            :class:`matrx.grid_world.GridWorld` blocks the agent performing other
            actions. By default this is 1, meaning that all actions of this type will take
            both the tick in which it was decided upon and the subsequent tick.
            When the agent is blocked / busy with an action, only the
            :meth:`matrx.agents.agent_brain.AgentBrain.filter_observations` method is called for that agent, and the
            :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method is skipped.
            This means that agents that are busy with an action can only perceive the world but not decide on
            a new action untill the action has completed.
            An agent can overwrite the duration of an action by returning the ``action_duration`` in the ``action_kwargs``
            in the :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method, as so:
            ``return >action_name<, {'action_duration': >ticks<}``
        Notes
        -----
        The actual carrying mechanism of objects is implemented in the
        :class:`matrx.actions.move_actions.Move` actions: whenever an agent moves
        who holds objects, those objects it is holding are also moved with it.
        """
    
    def __init__(self, action_duration=0):
        super().__init__(action_duration)

    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        """ Checks if the object can be dropped.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            :class:`matrx.objects.env_object.EnvObject` is dropped.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when checking if an
            action can be performed. Note that this is the State of the
            entire world, not that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            dropped. When not given the last object that was grabbed is
            dropped.
        drop_range : int (Optional. Default: np.inf)
            The range in which the object can be dropped, with the agent's
            location at its center.
        Returns
        -------
        DropObjectResult
            Depicts the action's expected success or failure and reason for
            that result.
            See :class:`matrx.actions.object_actions.DropObjectResult` for
            the results it can contain.
        """
        reg_ag = grid_world.registered_agents[agent_id]
        drop_range = 1 if 'drop_range' not in kwargs else kwargs['drop_range']
        #other_human = world_state[{"name": kwargs['human_name']}]
        #other_agent_id = world_state[{"name": "RescueBot"}]['obj_id']
        #other_agent = grid_world.registered_agents[other_agent_id]

        print("_is_possible?")
              
        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            # If there is already an object in this space, drop not possible
            if kwargs['object_id'] is None:
                return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT, False)
            obj_id = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            obj_id = reg_ag.is_carrying[-1].obj_id
        else:
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT, False)

        return _possible_drop(grid_world, agent_id=agent_id, obj_id=obj_id, drop_range=drop_range)

            

    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        """ Drops the carried object.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            :class:`matrx.objects.env_object.EnvObject` is dropped.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when performing an
            action. Note that this is the State of the entire world, not
            that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            dropped. When not given the last object that was grabbed is
            dropped.
        drop_range : int (Optional. Default: np.inf)
            The range in which the object can be dropped, with the agent's
            location at its center.
        Returns
        -------
        DropObjectResult
            The :class:`matrx.actions.action.ActionResult` depicting the
            action's expected success or failure and reason for that result.
            See :class:`matrx.actions.object_actions.DropObjectResult` for
            the results it can contain.
        Raises
        ------
        Exception
            When the object is said to be dropped inside the agent's location,
            but the agent and object are intraversable. No other intraversable
            objects can be on the same location.
        """
        reg_ag = grid_world.registered_agents[agent_id]
        if kwargs['human_name'] in agent_id and len(reg_ag.is_carrying)<2:
            reg_ag.change_property("img_name", "/images/rescue-man-final3.svg")
        if 'bot' in agent_id:
            reg_ag.change_property("img_name", "/images/robot-final4.svg")

        # fetch range from kwargs
        drop_range = 1 if 'drop_range' not in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
            env_obj = [obj for obj in reg_ag.is_carrying if obj.obj_id == obj_id][0]
        elif len(reg_ag.is_carrying) > 0:
            env_obj = reg_ag.is_carrying[-1]
        else:
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT_CARRIED, False)

        # check that it is even possible to drop this object somewhere
        if not env_obj.is_traversable and not reg_ag.is_traversable and drop_range == 0:
            raise Exception(
                f"Intraversable agent {reg_ag.obj_id} can only drop the intraversable object {env_obj.obj_id} at its "
                f"own location (drop_range = 0), but this is impossible. Enlarge the drop_range for the DropAction to "
                f"atleast 1")

        # check if we can drop it at our current location
        curr_loc_drop_poss = _is_drop_poss(grid_world, env_obj, reg_ag.location, agent_id)

        # drop it on the agent location if possible
        if curr_loc_drop_poss:
            return _act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=reg_ag.location)

        # if the agent location was the only within range, return a negative action result
        elif not curr_loc_drop_poss and drop_range == 0:
            return DropObjectResult(DropObjectResult.RESULT_OBJECT, False)

        # Try finding other drop locations from close to further away around the agent
        drop_loc = _find_drop_loc(grid_world, reg_ag, env_obj, drop_range, reg_ag.location)

        # If we didn't find a valid drop location within range, return a negative action result
        if not drop_loc:
            return DropObjectResult(DropObjectResult.RESULT_OBJECT, False)

        return _act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=drop_loc)


class DropObjectResult(ActionResult):
    """ ActionResult for a DropObjectAction.
    The results uniquely for GrabObjectAction are (as class constants):
    * RESULT_SUCCESS: When the object is successfully dropped.
    * RESULT_NO_OBJECT: When there is no object in the agent's inventory.
    * RESULT_NONE_GIVEN: When the given obj_id is not being carried by the
      agent.
    * RESULT_OBJECT: When the object was intended to drop on the agent's
      location and this was not possible or when no suitable drop location
      could be found.
    * RESULT_UNKNOWN_OBJECT_TYPE: When the object id does not exist (anymore).
    * RESULT_NO_OBJECT_CARRIED: When no objects are carried by the agent.
    Parameters
    ----------
    result : str
        A string representing the reason for the (expected) success or fail of
        an :class:`matrx.actions.object_actions.DropObjectAction`.
    succeeded : bool
        A boolean representing the (expected) success or fail of a
        :class:`matrx.actions.object_actions.DropObjectAction`.
    See Also
    --------
    GrabObjectAction
    """

    """ Result when dropping the object succeeded. """
    RESULT_SUCCESS = 'Drop action success'

    """ Result when there is not object in the agent's inventory. """
    RESULT_NO_OBJECT = 'The item is not carried'

    """ Result when the specified object is not in the agent's inventory. """
    RESULT_NONE_GIVEN = "'None' used as input id"

    """ Result when the specified object should be dropped on an agent. """
    RESULT_AGENT = 'Cannot drop item on an agent'

    """ Result when the specified object should be dropped on an intraversable 
    object."""
    RESULT_OBJECT = 'Cannot drop item on another intraversable object'

    """ Result when the specified object does not exist (anymore). """
    RESULT_UNKNOWN_OBJECT_TYPE = 'Cannot drop item on an unknown object'

    """ Result when the agent is not carrying anything. """
    RESULT_NO_OBJECT_CARRIED = 'Cannot drop object when none carried'

    def __init__(self, result, succeeded, obj_id=None):
        super().__init__(result, succeeded)
        self.obj_id = obj_id

class CarryObjectTogether(Action):
    """ Carries objects together.
    The action that can pick up / grab and hold an
    :class:`matrx.objects.env_object.EnvObject`. Cannot be performed on agents
    (including the agent performing the action). After grabbing / picking up,
    the object is automatically added to the agent's inventory and removed from
    the :class:`matrx.grid_world.GridWorld`.
    Parameters
    ----------
    action_duration : int
        Optional, default: ``1``. Should be zero or larger.
        The default duration of this action in ticks during which the
        :class:`matrx.grid_world.GridWorld` blocks the agent performing other
        actions. By default this is 1, meaning that all actions of this type will take
        both the tick in which it was decided upon and the subsequent tick.
        When the agent is blocked / busy with an action, only the
        :meth:`matrx.agents.agent_brain.AgentBrain.filter_observations` method is called for that agent, and the
        :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method is skipped.
        This means that agents that are busy with an action can only perceive the world but not decide on
        a new action untill the action has completed.
        An agent can overwrite the duration of an action by returning the ``action_duration`` in the ``action_kwargs``
        in the :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method, as so:
        ``return >action_name<, {'action_duration': >ticks<}``
    Notes
    -----
    The actual carrying mechanism of objects is implemented in the
    :class:`matrx.actions.move_actions.Move` actions: whenever an agent moves
    who holds objects, those objects it is holding are also moved with it.
    """

    def __init__(self, action_duration=0):
        super().__init__(action_duration)

    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        """ Checks if the object can be grabbed.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            object is sought according to the `object_id` parameter.
        agent_id: str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when checking if an
            action can be performed. Note that this is the State of the
            entire world, not that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            grabbed. When not given, a random object within range is selected.
        grab_range : int (Optional. Default: np.inf)
            The range in which the :class:`matrx.objects.env_object.EnvObject`
            should be in to be grabbed.
        max_objects : int (Optional. Default: np.inf)
            The maximum of objects the agent can carry.
        Returns
        -------
        GrabObjectResult
            Depicts the action's expected success or failure and reason for
            that result.
            See :class:`matrx.actions.object_actions.GrabObjectResult` for
            the results it can contain.
        """
        # Set default values check
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        grab_range = np.inf if 'grab_range' not in kwargs else kwargs['grab_range']
        max_objects = np.inf if 'max_objects' not in kwargs else kwargs['max_objects']
        other_agent = world_state[{"name": "RescueBot"}]
        
        if object_id and get_distance(other_agent['location'], world_state[object_id]['location']) > grab_range:
            return GrabObjectResult(GrabObjectResult.NOT_IN_RANGE, False)
        else:
            return _is_possible_grab(grid_world, agent_id=agent_id, object_id=object_id, grab_range=grab_range,
                                 max_objects=max_objects)

    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        """ Grabs an object.
        Alters the properties of the agent doing the grabbing, and the object
        being grabbed (and carried), such that the agent's inventory contains
        the entire object and the object being carried properties contains the
        agent's id.
        The grabbed object is removed from the world, and will only exist
        inside of the agent's inventory.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            object is sought according to the `object_id` parameter.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when performing an
            action. Note that this is the State of the entire world, not
            that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            grabbed. When not given, a random object within range is selected.
        grab_range : int (Optional. Default: np.inf)
            The range in which the :class:`matrx.objects.env_object.EnvObject`
            should be in to be grabbed.
        max_objects : int (Optional. Default: np.inf)
            The maximum of objects the agent can carry.
        Returns
        -------
        GrabObjectResult
            Depicts the action's expected success or failure and reason for
            that result.
            See :class:`matrx.actions.object_actions.GrabObjectResult` for
            the results it can contain.
        Notes
        -----
        A grabbed object resides inside the inventory of an agent, not directly
        in the world any longer. Hence, if the agent is removed, so is its
        inventory and all objects herein.
        """

        # Additional check
        assert 'object_id' in kwargs.keys()
        assert 'grab_range' in kwargs.keys()
        assert 'max_objects' in kwargs.keys()

        # if possible:
        object_id = kwargs['object_id']  # assign

        # Loading properties
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        env_obj = grid_world.environment_objects[object_id]  # Environment object

        # Updating properties
        env_obj.carried_by.append(agent_id)
        reg_ag.is_carrying.append(env_obj)  # we add the entire object!

        other_agent_id = world_state[{"name": "RescueBot"}]['obj_id']

        # if we want to change objects, we need to change the grid_world object 
        other_agent = grid_world.registered_agents[other_agent_id]
        agent = grid_world.registered_agents[agent_id]

        # make the other agent invisible 
        other_agent.change_property("visualize_opacity", 0)

        # change our image 
        
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if 'critical' in object_id and kwargs['human_name'] in agent_id:
            # change our image 
            agent.change_property("img_name", "/images/carry-critical-final.svg")
        if 'mild' in object_id and kwargs['human_name'] in agent_id:
            agent.change_property("img_name", "/images/carry-mild-final.svg")

        # Remove it from the grid world (it is now stored in the is_carrying list of the AgentAvatar
        succeeded = grid_world.remove_from_grid(object_id=env_obj.obj_id, remove_from_carrier=False)
        if not succeeded:
            return GrabObjectResult(GrabObjectResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD.replace("{OBJECT_ID}",
                                                                                                env_obj.obj_id), False)

        # Updating Location (done after removing from grid, or the grid will search the object on the wrong location)
        env_obj.location = reg_ag.location

        return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, True)


class GrabObjectResult(ActionResult):
    """ActionResult for a GrabObjectAction
    The results uniquely for GrabObjectAction are (as class constants):
    * RESULT_SUCCESS: When the object can be successfully grabbed.
    * RESULT_NO_OBJECT: When `object_id` is not given.
    * RESULT_CARRIES_OBJECT: When the agent already carries the maximum nr.
      objects.
    * NOT_IN_RANGE: When `object_id` not within range.
    * RESULT_AGENT: If the `object_id` is that of an agent.
    * RESULT_OBJECT_CARRIED: When the object is already carried by another
      agent.
    * RESULT_OBJECT_UNMOVABLE: When the object is not movable.
    * RESULT_UNKNOWN_OBJECT_TYPE: When the `object_id` does not exists in the
      :class:`matrx.grid_world.GridWorld`.
    * FAILED_TO_REMOVE_OBJECT_FROM_WORLD: When the grabbed object cannot be
      removed from the :class:`matrx.grid_world.GridWorld`.
    Parameters
    ----------
    result : str
        A string representing the reason for a
        :class:`matrx.actions.object_actions.GrabObjectAction` (expected)
        success or fail.
    succeeded : bool
        A boolean representing the (expected) success or fail of a
        :class:`matrx.actions.object_actions.GrabObjectAction`.
    See Also
    --------
    GrabObjectAction
    """

    """ Result when the object can be successfully grabbed. """
    RESULT_SUCCESS = 'Grab action success'

    """ Result when the grabbed object cannot be removed from the 
    :class:`matrx.grid_world.GridWorld`. """
    FAILED_TO_REMOVE_OBJECT_FROM_WORLD = 'Grab action failed; could not remove object with id {OBJECT_ID} from grid.'

    """ Result when the specified object is not within range. """
    NOT_IN_RANGE = 'Object not in range'

    """ Result when the specified object is an agent. """
    RESULT_AGENT = 'This is an agent, cannot be picked up'

    """ Result when no object was specified. """
    RESULT_NO_OBJECT = 'No Object specified'

    """ Result when the agent is at its maximum carrying capacity. """
    RESULT_CARRIES_OBJECT = 'Agent already carries the maximum amount of objects'

    """ Result when the specified object is already carried by another agent. 
    """
    RESULT_OBJECT_CARRIED = 'Object is already carried by {AGENT_ID}'

    """ Result when the specified object does not exist in the 
    :class:`matrx.grid_world.GridWorld` """
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'

    """ Result when the specified object is not movable. """
    RESULT_OBJECT_UNMOVABLE = 'Object is not movable'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)

class DropObjectTogether(Action):
    """ Drops a carried object.
        The action that can drop an :class:`matrx.objects.env_object.EnvObject`
        that is in an agent's inventory. After dropping, the object is added to the
        :class:`matrx.grid_world.GridWorld`.
        Parameters
        ----------
        action_duration : int
            Optional, default: ``1``. Should be zero or larger.
            The default duration of this action in ticks during which the
            :class:`matrx.grid_world.GridWorld` blocks the agent performing other
            actions. By default this is 1, meaning that all actions of this type will take
            both the tick in which it was decided upon and the subsequent tick.
            When the agent is blocked / busy with an action, only the
            :meth:`matrx.agents.agent_brain.AgentBrain.filter_observations` method is called for that agent, and the
            :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method is skipped.
            This means that agents that are busy with an action can only perceive the world but not decide on
            a new action untill the action has completed.
            An agent can overwrite the duration of an action by returning the ``action_duration`` in the ``action_kwargs``
            in the :meth:`matrx.agents.agent_brain.AgentBrain.decide_on_action` method, as so:
            ``return >action_name<, {'action_duration': >ticks<}``
        Notes
        -----
        The actual carrying mechanism of objects is implemented in the
        :class:`matrx.actions.move_actions.Move` actions: whenever an agent moves
        who holds objects, those objects it is holding are also moved with it.
        """
    
    def __init__(self, action_duration=0):
        super().__init__(action_duration)

    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        """ Checks if the object can be dropped.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            :class:`matrx.objects.env_object.EnvObject` is dropped.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when checking if an
            action can be performed. Note that this is the State of the
            entire world, not that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            dropped. When not given the last object that was grabbed is
            dropped.
        drop_range : int (Optional. Default: np.inf)
            The range in which the object can be dropped, with the agent's
            location at its center.
        Returns
        -------
        DropObjectResult
            Depicts the action's expected success or failure and reason for
            that result.
            See :class:`matrx.actions.object_actions.DropObjectResult` for
            the results it can contain.
        """
        reg_ag = grid_world.registered_agents[agent_id]
        drop_range = 1 if 'drop_range' not in kwargs else kwargs['drop_range']
        other_agent_id = world_state[{"name": "RescueBot"}]['obj_id']
        other_agent = grid_world.registered_agents[other_agent_id]
        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            obj_id = reg_ag.is_carrying[-1].obj_id
        else:
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT, False)
        if 'healthy' in obj_id and other_agent.properties['visualization']['opacity']!=0 or 'mild' in obj_id and other_agent.properties['visualization']['opacity']!=0:
            return DropObjectResult(DropObjectResult.RESULT_UNKNOWN_OBJECT_TYPE, False)            
        else:
            return _possible_drop(grid_world, agent_id=agent_id, obj_id=obj_id, drop_range=drop_range)

    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        """ Drops the carried object.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            :class:`matrx.objects.env_object.EnvObject` is dropped.
        agent_id : str
            The string representing the unique identifier that represents the
            agent performing this action.
        world_state : State
            The State object representing the entire world. Can be used to
            simplify search of objects and properties when performing an
            action. Note that this is the State of the entire world, not
            that of the agent performing the action.
        object_id : str (Optional. Default: None)
            The string representing the unique identifier of the
            :class:`matrx.objects.env_object.EnvObject` that should be
            dropped. When not given the last object that was grabbed is
            dropped.
        drop_range : int (Optional. Default: np.inf)
            The range in which the object can be dropped, with the agent's
            location at its center.
        Returns
        -------
        DropObjectResult
            The :class:`matrx.actions.action.ActionResult` depicting the
            action's expected success or failure and reason for that result.
            See :class:`matrx.actions.object_actions.DropObjectResult` for
            the results it can contain.
        Raises
        ------
        Exception
            When the object is said to be dropped inside the agent's location,
            but the agent and object are intraversable. No other intraversable
            objects can be on the same location.
        """
        reg_ag = grid_world.registered_agents[agent_id]
        other_agent_id = world_state[{"name": "RescueBot"}]['obj_id']
        other_agent = grid_world.registered_agents[other_agent_id]
        agent = grid_world.registered_agents[agent_id]
        # fetch range from kwargs
        drop_range = 1 if 'drop_range' not in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
            env_obj = [obj for obj in reg_ag.is_carrying if obj.obj_id == obj_id][0]
        elif len(reg_ag.is_carrying) > 0:
            env_obj = reg_ag.is_carrying[-1]
        else:
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT_CARRIED, False)
        
        other_agent.change_property("location", agent.properties['location'])

        # make the other agent visible again 
        other_agent.change_property("visualize_opacity", 1)

        # change the agent image back to default 
        agent.change_property("img_name", "/images/rescue-man-final3.svg")

        # check that it is even possible to drop this object somewhere
        if not env_obj.is_traversable and not reg_ag.is_traversable and drop_range == 0:
            raise Exception(
                f"Intraversable agent {reg_ag.obj_id} can only drop the intraversable object {env_obj.obj_id} at its "
                f"own location (drop_range = 0), but this is impossible. Enlarge the drop_range for the DropAction to "
                f"atleast 1")

        # check if we can drop it at our current location
        curr_loc_drop_poss = _is_drop_poss(grid_world, env_obj, reg_ag.location, agent_id)

        # drop it on the agent location if possible
        if curr_loc_drop_poss:
            return _act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=reg_ag.location)

        # if the agent location was the only within range, return a negative action result
        elif not curr_loc_drop_poss and drop_range == 0:
            return DropObjectResult(DropObjectResult.RESULT_OBJECT, False)

        # Try finding other drop locations from close to further away around the agent
        drop_loc = _find_drop_loc(grid_world, reg_ag, env_obj, drop_range, reg_ag.location)

        # If we didn't find a valid drop location within range, return a negative action result
        if not drop_loc:
            return DropObjectResult(DropObjectResult.RESULT_OBJECT, False)

        return _act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=drop_loc)



def _is_possible_grab(grid_world, agent_id, object_id, grab_range, max_objects):
    """ Private MATRX method.
    Checks if an :class:`matrx.objects.env_object.EnvObject` can be
    grabbed by an agent.
    Parameters
    ----------
    grid_world : GridWorld
        The :class:`matrx.grid_world.GridWorld` instance in which the
        object is sought according to the `object_id` parameter.
    agent_id : str
        The string representing the unique identified that represents the
         agent performing this action.
    object_id : str
        Optional. Default: ``None``
        The string representing the unique identifier of the
        :class:`matrx.objects.env_object.EnvObject` that should be
        grabbed. When not given, a random object within range is selected.
    grab_range : int
        Optional. Default: ``np.inf``
        The range in which the to be grabbed
        :class:`matrx.objects.env_object.EnvObject` should be in.
    max_objects : int
        Optional. Default: ``np.inf``
        The maximum of objects the agent can carry.
    Returns
    -------
    GrabObjectResult
        Depicts the action's expected success or failure and reason for
        that result.
        Can contain the following results:
        * RESULT_SUCCESS: When the object can be successfully grabbed.
        * RESULT_NO_OBJECT : When `object_id` is not given.
        * RESULT_CARRIES_OBJECT: When the agent already carries the maximum
          nr. objects.
        * NOT_IN_RANGE: When `object_id` not within range.
        * RESULT_AGENT: If the `object_id` is that of an agent.
        * RESULT_OBJECT_CARRIED: When the object is already carried by
          another agent.
        * RESULT_OBJECT_UNMOVABLE: When the object is not movable.
        * RESULT_UNKNOWN_OBJECT_TYPE: When the `object_id` does not exists
          in the :class:`matrx.grid_world.GridWorld`.
    """

    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    if object_id is None:
        return GrabObjectResult(GrabObjectResult.RESULT_NO_OBJECT, False)

    # Already carries an object
    if len(reg_ag.is_carrying) >= max_objects:
        return GrabObjectResult(GrabObjectResult.RESULT_CARRIES_OBJECT, False)

    # Go through all objects at the desired locations
    objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type="*", sense_range=grab_range)
    objects_in_range.pop(agent_id)

    # Set random object in range
    if not object_id:
        # Remove all non objects from the list
        for obj in list(objects_in_range.keys()):
            if obj not in grid_world.environment_objects.keys():
                objects_in_range.pop(obj)

        # Select a random object
        if objects_in_range:
            object_id = grid_world.rnd_gen.choice(list(objects_in_range.keys()))
        else:
            return GrabObjectResult(GrabObjectResult.NOT_IN_RANGE, False)

    # Check if object is in range
    if object_id not in objects_in_range:
        return GrabObjectResult(GrabObjectResult.NOT_IN_RANGE, False)

    # Check if object_id is the id of an agent
    if object_id in grid_world.registered_agents.keys():
        # If it is an agent at that location, grabbing is not possible
        return GrabObjectResult(GrabObjectResult.RESULT_AGENT, False)

    # Check if it is an object
    if object_id in grid_world.environment_objects.keys():
        env_obj = grid_world.environment_objects[object_id]  # Environment object
        # Check if the object is not carried by another agent
        if len(env_obj.carried_by) != 0:
            return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_CARRIED.replace("{AGENT_ID}",
                                                                                   str(env_obj.carried_by)),
                                    False)
        elif not env_obj.properties["is_movable"]:
            return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_UNMOVABLE, False)
        else:
            # Success
            return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, True)
    else:
        return GrabObjectResult(GrabObjectResult.RESULT_UNKNOWN_OBJECT_TYPE, False)

def _act_drop(grid_world, agent, env_obj, drop_loc):
    """ Private MATRX method.
        Drops the carried object.
        Parameters
        ----------
        grid_world : GridWorld
            The :class:`matrx.grid_world.GridWorld` instance in which the
            object is dropped.
        agent : AgentBody
            The :class:`matrx.objects.agent_body.AgentBody` of the agent who
            drops the object.
        env_obj : EnvObject
            The :class:`matrx.objects.env_object.EnvObject` to be dropped.
        drop_loc : [x, y]
            The drop location.
        Returns
        -------
        DropObjectResult
            The :class:`matrx.actions.action.ActionResult` depicting the
            action's expected success or failure and reason for that result.
            Returns the following results:
            * RESULT_SUCCESS: When the object is successfully dropped.
        """

    # Updating properties
    agent.is_carrying.remove(env_obj)
    env_obj.carried_by.remove(agent.obj_id)

    # We return the object to the grid location we are standing at without registering a new ID
    env_obj.location = drop_loc
    grid_world._register_env_object(env_obj, ensure_unique_id=False)

    return DropObjectResult(DropObjectResult.RESULT_SUCCESS, True)


def _is_drop_poss(grid_world, env_obj, drop_location, agent_id):
    """ Private MATRX method.
    A breadth first search starting from the agent's location to find the
    closest valid drop location.
    Parameters
    ----------
    grid_world : GridWorld
        The :class:`matrx.grid_world.GridWorld` instance in which the
        object is dropped.
    env_obj : EnvObject
        The :class:`matrx.objects.env_object.EnvObject` to be dropped.
    drop_range : int
        The range in which the object can be dropped.
    start_loc : [x, y]
        The location of the agent from which to start the search.
    agent_id : str
        The agent id of the agent who drops the object.
    Returns
    -------
    boolean
        False if no valid drop location can be found, otherwise the [x,y]
        coordinates of the closest drop location.
    """

    # Count the intraversable objects at the current location if we would drop the
    # object here
    objs_at_loc = grid_world.get_objects_in_range(drop_location, object_type="*", sense_range=0)

    # Remove area objects from the list
    for key in list(objs_at_loc.keys()):
        if AreaTile.__name__ in objs_at_loc[key].class_inheritance:
            objs_at_loc.pop(key)

    # Remove the agent who drops the object from the list (an agent can always drop the
    # traversable object its carrying at its feet, even if the agent is intraversable)
    if agent_id in objs_at_loc.keys():
        objs_at_loc.pop(agent_id)

    in_trav_objs_count = 1 if not env_obj.is_traversable else 0
    in_trav_objs_count += len([obj for obj in objs_at_loc if not objs_at_loc[obj].is_traversable])

    # check if we would have an in_traversable object and other objects in
    # the same location (which is impossible)
    if in_trav_objs_count >= 1 and (len(objs_at_loc) + 1) >= 2:
        return False
    else:
        return True


def _possible_drop(grid_world, agent_id, obj_id, drop_range):
    """ Private MATRX method.
    Checks if an :class:`matrx.objects.env_object.EnvObject` can be
    dropped by an agent.
    Parameters
    ----------
    grid_world : GridWorld
        The :class:`matrx.grid_world.GridWorld` instance in which the
        object is dropped.
    agent_id: str
        The string representing the unique identified that represents the
        agent performing this action.
    obj_id: str
        The string representing the unique identifier of the
        :class:`matrx.objects.env_object.EnvObject` that should be
        dropped.
    drop_range : int
        The range in which the :class:`matrx.objects.env_object.EnvObject`
        should be dropped in.
    Returns
    -------
    DropObjectResult
        The :class:`matrx.actions.action.ActionResult` depicting the
        action's expected success or failure and reason for that result.
        Returns the following results:
        * RESULT_SUCCESS: When the object can be successfully dropped.
        * RESULT_NONE_GIVEN: When the given obj_id is not being carried by
          the agent.
        * RESULT_NO_OBJECT: When no obj_id is given.
    """
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location
    loc_obj_ids = grid_world.grid[loc_agent[1], loc_agent[0]]

    # No object given
    if not obj_id:
        return DropObjectResult(DropObjectResult.RESULT_NONE_GIVEN, False)

    # No object with that name
    if isinstance(obj_id, str) and not any([obj_id == obj.obj_id for obj in reg_ag.is_carrying]):
        return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT, False)

    if len(loc_obj_ids) == 1:
        return DropObjectResult(DropObjectResult.RESULT_SUCCESS, True)

    # TODO: incorporate is_possible check from DropAction.mutate is_possible here

    return DropObjectResult(DropObjectResult.RESULT_SUCCESS, True)


def _find_drop_loc(grid_world, agent, env_obj, drop_range, start_loc):
    """ Private MATRX method.
    A breadth first search starting from the agent's location to find the closest valid drop location.
    Parameters
    ----------
    grid_world : GridWorld
        The GridWorld instance in which the object is dropped.
    agent : AgentBody
        The AgentBody of the agent who drops the object.
    env_obj : EnvObject
        The EnvObject to be dropped.
    drop_range : int
        The range in which the object can be dropped.
    start_loc : [x, y]
        The location of the agent from which to start the search.
    Returns
    -------
    boolean
        False if no valid drop location can be found, otherwise the [x,y] coordinates of the closest drop location.
    """
    queue = collections.deque([[start_loc]])
    seen = {start_loc}

    width = grid_world.shape[0]
    height = grid_world.shape[1]

    while queue:
        path = queue.popleft()
        x, y = path[-1]

        # check if we are still within drop_range
        if get_distance([x, y], start_loc) > drop_range:
            return False

        # check if we can drop at this location
        if _is_drop_poss(grid_world, env_obj, [x, y], agent.obj_id):
            return [x, y]

        # queue unseen neighbouring tiles
        for x2, y2 in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= x2 < width and 0 <= y2 < height and (x2, y2) not in seen:
                queue.append(path + [(x2, y2)])
                seen.add((x2, y2))
    return False