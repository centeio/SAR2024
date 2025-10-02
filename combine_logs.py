import os
import pandas as pd
import traceback

logs_dir = 'logs'
excluded_dirs = {'PA2', 'PA55'}

all_actions = []
all_final = []
all_allocation = []
all_preferences = []

def calculate_victim_counts(actions_df, human_areas_final, agent_areas_final, agent_type, agent_name):
    results = {}
    vics_human = 0
    vics_human_plan = 0
    vics_human_not_plan = 0
    vics_agent = 0


    filtered_actions = actions_df[actions_df['agent_name'] == agent_name]
    drops = filtered_actions[(filtered_actions['action'] == 'drop_victim') & (filtered_actions['at_drop_off'] == True)]

    for _, row in drops.iterrows():
        if row['agent_type'] == 'human':
            vics_human += 1
            if row['vic_area'] in eval(human_areas_final):
                vics_human_plan += 1
            else:
                vics_human_not_plan += 1
        else:
            vics_agent += 1

        compliance = vics_human_plan / vics_human if vics_human > 0 else None

    print(filtered_actions['PID'].iloc[0],agent_type,vics_human,vics_human_plan,vics_human_not_plan,vics_agent,compliance)

    results = {
        'PID': filtered_actions['PID'].iloc[0],
        'agent_type': agent_type,
        'vics_human': vics_human,
        'vics_human_plan': vics_human_plan,
        'vics_human_not_plan': vics_human_not_plan,
        'vics_agent': vics_agent,
        'compliance': compliance
    }

    return results


def process_allocation(allocation_df):
    records = []
    grouped = allocation_df.groupby(['PID', 'agent_type', 'agent_name'])

    for (pid, agent_type, agent_name), group in grouped:
        group = group.sort_values('local_time')
        condition = group['condition'].iloc[0]

        if condition == 'mission_comm' and len(group) == 2:
            initial = group.iloc[0]
            final = group.iloc[1]

            record = {
                'PID': pid,
                'condition': condition,
                'agent_type': agent_type,
                'agent_name': agent_name,
                'local_time': final['local_time'],
                'human_areas_initial': initial['human_areas'],
                'agent_areas_initial': initial['agent_areas'],
                'human_areas_final': final['human_areas'],
                'agent_areas_final': final['agent_areas'],
                'changes': final['changes'],
            }

        elif condition == 'mission_nocomm' and len(group) == 1:
            row = group.iloc[0]
            record = {
                'PID': pid,
                'condition': condition,
                'agent_type': agent_type,
                'agent_name': agent_name,
                'local_time': row['local_time'],
                'human_areas_initial': row['human_areas'],
                'agent_areas_initial': row['agent_areas'],
                'human_areas_final': row['human_areas'],
                'agent_areas_final': row['agent_areas'],
                'changes': -1,
            }

        else:
            print(f"Unexpected row count ({len(group)}) for PID={pid}, agent_type={agent_type}, agent_name={agent_name}")
            continue

        records.append(record)

    return pd.DataFrame(records)

all_counts_list = []  # global list for all participants

for subdir in os.listdir(logs_dir):
    path = os.path.join(logs_dir, subdir)

    if subdir.startswith("PA") and subdir not in excluded_dirs and os.path.isdir(path):
        try:
            pid = subdir
            actions_path = os.path.join(path, 'actions.csv')
            final_path = os.path.join(path, 'final.csv')
            allocation_path = os.path.join(path, 'allocation.csv')
            preferences_path = os.path.join(path, 'preferences.csv')

            # Read and collect actions
            actions_df = pd.read_csv(actions_path)
            all_actions.append(actions_df)

            # Read and collect final
            final_df = pd.read_csv(final_path)
            # There is an error in the logs of the following columns, so we remove them
            final_df = final_df.drop(
                columns=[
                    'human_vics_saved_abs',
                    'human_vics_saved_rel',
                    'agent_vics_saved_abs',
                    'agent_vics_saved_rel',
                    'agent_vics_saved_by_human_abs',
                    'agent_vics_saved_by_human_rel',
                    'compliance'
                ]
            )            
            
            all_final.append(final_df)


            # Read and collect allocation
            allocation_df = pd.read_csv(allocation_path)
            all_allocation.append(allocation_df)

            # We recalculate the wrong metrics mentioned above based on the actions
            processed_alloc = process_allocation(allocation_df)

            counts_list = []

            for agent_type in ['will', 'nowill']:
                mission_alloc = processed_alloc[processed_alloc['agent_type'] == agent_type].iloc[0]
                human_areas_final = mission_alloc['human_areas_final']
                agent_areas_final = mission_alloc['agent_areas_final']

                agent_name_mission = actions_df.loc[actions_df['agent_type'] == agent_type, 'agent_name'].iloc[0]

                counts = calculate_victim_counts(
                    actions_df, human_areas_final, agent_areas_final,
                    agent_type, agent_name_mission
                )
                counts_list.append(counts)

            # convert per-participant counts to DataFrame
            all_counts = pd.DataFrame(counts_list)
            all_counts_list.append(all_counts)

            # Read and pivot preferences
            prefs_df = pd.read_csv(preferences_path)
            prefs_df.columns = [col.strip() for col in prefs_df.columns]

            prefs_df = prefs_df.tail(4).drop_duplicates(subset='pref_id', keep='last')

            if 'pref_id' in prefs_df.columns and 'preference_num' in prefs_df.columns:
                prefs_df['dummy_index'] = 0
                pivot = prefs_df.pivot(index='dummy_index', columns='pref_id', values='preference_num')
                pivot.columns = [f'pref_{col}' for col in pivot.columns]
                pivot.insert(0, 'PID', pid)
                all_preferences.append(pivot)
            else:
                print(f"Skipping preferences for {pid}: required columns missing: {prefs_df.columns.tolist()}")

        except Exception as e:
            print(f"Error processing {subdir}: {type(e).__name__}: {e}")
            traceback.print_exc()

# Save combined actions
combined_actions = pd.concat(all_actions, ignore_index=True)
combined_actions.to_csv('combined_actions.csv', index=False)

# Process allocation
combined_allocation_raw = pd.concat(all_allocation, ignore_index=True)
processed_allocation = process_allocation(combined_allocation_raw)

# Save victim counts
combined_counts = pd.concat(all_counts_list, ignore_index=True)
#combined_counts.to_csv('combined_victim_counts.csv', index=False)

# Combine final
df_final = pd.concat(all_final, ignore_index=True)

# Merge allocation + final on full key
combined_dataset = processed_allocation.merge(
    df_final,
    on=['PID', 'condition', 'agent_type', 'agent_name'],
    how='inner'
)
# Merge combined_counts into combined_dataset on PID and agent_type
combined_dataset = combined_dataset.merge(
    combined_counts,
    on=['PID', 'agent_type'],
    how='left',  # use 'left' to keep all rows in combined_dataset
    suffixes=('', '_count')  # prevent column name conflicts
)

combined_dataset.to_csv('combined_objective.csv', index=False)

# Combine and save preferences
combined_preferences = pd.concat(all_preferences, ignore_index=True)
combined_preferences.to_csv('combined_preferences.csv', index=False)
