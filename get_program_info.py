from get_rehit_lib import connect_db
import sys
import json
from collections import defaultdict

EITHER = 2
LEFT = 4
RIGHT = 3

DRIVER_SIDE = 5
PASSENGER_SIDE = 6

FUEL_FILLER = 7
OPPOSITE_FUEL_FILLER = 8


def get_program_info(program_id):
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)

    sql = """
	SELECT [Program].[platform], [Program].[program], [Program].[nameplate], [Program].[year], [Program].[comments], [Regions].[name] AS [region] FROM Program 
				LEFT JOIN [Regions] ON [Regions].[id]=[Program].[regionid] 
				WHERE [Program].[id]=%d
	"""
    cursor.execute(sql, (program_id,))
    r = cursor.fetchone()
    if not r:
        print "Cannot find program with id %d", program_id
        return

    platform = r["platform"]
    nameplate = r["nameplate"]
    program = r["program"]
    region = r["region"]
    year = r["year"]
    comments = r["comments"]

    conn.close()

    return {
        "platform": platform,
        "nameplate": nameplate,
        "program": program,
        "region": region,
        "year": year,
        "comments": comments
    }


def get_program_config(run_id):
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)
    sql = """
	SELECT * FROM [OptimizationRuns] WHERE [id]=%d
	"""
    cursor.execute(sql, (run_id,))
    r = cursor.fetchone()
    if not r:
        print "Cannot find program config with id %d", run_id
        return

    program_id = r["programId"]
    lib_id = r["libraryId"]
    relaxtime = r["relaxTime"]
    relaxspecs = r["relaxVehicleSpecs"]
    doubleprep = r["doublePrep"]
    maxhits = r["maxNumRehits"]
    maxtardiness = r["maxTardiness"]
    weekendshift = r["workWeekends"]
    holidayshift = r["workHolidays"]

    # relaxefacility = r["relaxmaxhits"]
    # relaxprep = r["relaxmaxpreps"]
    # cbb_cap = r["maxhitsperday"]
    # roush_cap = r["maxprepsperday"]

    # calendar_id = r["calendarid"]

    conn.close()

    return {
        "program_id": program_id,
        "rehit_lib_id": lib_id,
        "relax_time": relaxtime,
        "relax_specs": relaxspecs,
        "double_prep": doubleprep,
        "max_hits": maxhits,
        "max_tardiness": maxtardiness,
        "work_on_weekends": weekendshift,
        "work_on_holidays": holidayshift,
        # "relax_cbb_cap": relaxefacility,
        # "relax_roush_cap": relaxprep,
        # "cbb_cap": cbb_cap,
        # "roush_cap": roush_cap,
        # "calendar_id": calendar_id
    }


def get_control_model_info(program_id):
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)
    sql = """
	SELECT [ControlModel].[id], [ControlModel].[driverSideTestPositioningID] AS [driverSide],
				[ControlModel].[fuelFillerSideTestPositioningID] AS [fillerSide],
				 [Options].[name] AS optionname, [Feature].[name] as featurename FROM [ControlModel] 
				LEFT JOIN [ControlModelOptions] ON [ControlModel].[id]=[ControlModelOptions].[ControlModelid] 
				LEFT JOIN [Options] ON [ControlModelOptions].[optionid]=[Options].[id] 
				LEFT JOIN [Feature] ON [Feature].[id]=[Options].[featureid] 
				WHERE [ControlModel].[programid]= %d
				ORDER BY [ControlModel].[ordering], [Feature].[ordering]
	"""
    cursor.execute(sql, (program_id,))
    control_model_list = []
    control_model_feature_map = defaultdict(dict)
    for r in cursor:
        control_model_id = r["id"]
        if r["driverSide"] == 4:
            driver_side = "LEFT"
        else:
            driver_side = "RIGHT"

        if r["fillerSide"] == 4:
            filler_side = "LEFT"
        else:
            filler_side = "RIGHT"

        option_name = r["optionname"]
        feature_name = r["featurename"]

        control_model_feature_map[control_model_id][feature_name] = option_name
        control_model_feature_map[control_model_id]["driver_side"] = driver_side
        control_model_feature_map[control_model_id]["fuel_filler_side"] = filler_side

    conn.close()

    for k, v in control_model_feature_map.iteritems():
        control_model_list.append({
            "control_model_id": k,
            "specs": v
        })

    return control_model_list


def get_vehicle_info(program_id):
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)

    sql = """
	 SELECT [VehicleCandidate].[id], [VehicleCandidate].[name], [VehicleCandidate].[deliveryDate], [VehicleCandidate].[vehicleNumber], 
				[VehicleCandidateControlModel].[ControlModelID] FROM [VehicleCandidateControlModel]
				JOIN [VehicleCandidate] ON [VehicleCandidateControlModel].[vehicleCandidateid]=[VehicleCandidate].[id]
				WHERE [VehicleCandidate].[programid]=%d
				ORDER BY [VehicleCandidate].[id], [deliveryDate]
	"""
    cursor.execute(sql, (program_id,))
    vehicle_control_model_set = defaultdict(list)
    vehicle_general_info = defaultdict(dict)
    for r in cursor:
        vehicle_id = r["id"]
        delivery_date = r["deliveryDate"]
        display_number = r["vehicleNumber"]
        control_model_id = r["ControlModelID"]
        vehicle_tag = r["name"]

        vehicle_control_model_set[vehicle_id].append(control_model_id)
        vehicle_general_info[vehicle_id]["delivery_date"] = delivery_date
        vehicle_general_info[vehicle_id]["tag"] = vehicle_tag
        vehicle_general_info[vehicle_id]["display_number"] = display_number

    vehicle_list = []
    # map from control model id to specs
    control_model_list = get_control_model_info(program_id)
    control_model_map = {}
    for c in control_model_list:
        control_model_map[c["control_model_id"]] = c

    for k, v in vehicle_control_model_set.iteritems():
        model_set = [control_model_map[cid] for cid in v]
        vehicle_list.append({
            "vehicle_id": k,
            "display_number": vehicle_general_info[k]["display_number"],
            "tag": vehicle_general_info[k]["tag"],
            "delivery_date": vehicle_general_info[k]["delivery_date"],
            "model_set": model_set
        })

    conn.close()

    return vehicle_list


def get_deadline_info(program_id):
    # get the deadline identifiers
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)

    sql = """
    select * from UniversalDeadlines
    """
    cursor.execute(sql, (program_id,))
    deadline_map = {}
    for r in cursor:
        deadline_id = r["ID"]
        deadline_name = r["name"]
        is_deadline = r["isDeadline"]
        if is_deadline:
            deadline_map[deadline_id] = deadline_name
        else:
            deadline_map[deadline_id] = deadline_name + " START"

    cursor.close()

    return deadline_map


def get_safetymode_info():
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)

    sql = """
    SELECT [SafetyTest].[id], [SafetyTest].[code], [SafetyTest].[name],[SafetyTest].[req_signoff],[SafetyTest].[req_walkaround],[SafetyTest].[req_crash], [Subcategory].[code] AS [subcode],
				[Category].[name] AS [category] FROM [SafetyTest]
				JOIN [Subcategory] ON [SafetyTest].[subcategoryID]=[Subcategory].[id]
				JOIN [Category] ON [Category].[id]=[Subcategory].[categoryID]
	"""
    cursor.execute(sql)

    safety_mode_map = {}
    for r in cursor:
        mode_id = r["id"]
        safety_mode_map[mode_id] = r

    cursor.close()

    return safety_mode_map


def abs_position(relative_pos, driver_side, fuel_filler):
    if relative_pos==DRIVER_SIDE:
        if driver_side==EITHER:
            return relative_pos
        elif driver_side==LEFT:
            return LEFT
        else:
            return RIGHT
    elif relative_pos==PASSENGER_SIDE:
        if driver_side==EITHER:
            return relative_pos
        elif driver_side==LEFT:
            return RIGHT
        else:
            return LEFT
    elif relative_pos==FUEL_FILLER:
        if fuel_filler==LEFT:
            return LEFT
        else:
            return RIGHT
    elif relative_pos==OPPOSITE_FUEL_FILLER:
        if fuel_filler==LEFT:
            return RIGHT
        else:
            return LEFT
    else:
        return relative_pos


def get_test_info(program_id):
    # read in test information
    conn = connect_db()
    cursor = conn.cursor(as_dict=True)

    deadline_map = get_deadline_info(program_id)
    control_model_map = get_control_model_info(program_id)

    sql = """
    SELECT [ControlModelTestPairRequirements].[id] AS testID,[ControlModelTestPairRequirements].[req_witness], [ControlModelTestPairRequirements].[deadlineID], [SafetyTest].[id] AS [safetyID], [SafetyTest].[min_kph],[SafetyTest].[max_kph], [SafetyTest].[rehitCategoryID],
				[SafetyTest].[positionID], [ControlModelTestPairRequirements].[controlModelID], [ControlModel].[driverSideTestPositioningID] AS [driverSide],
				[ControlModel].[fuelFillerSideTestPositioningID] AS [fillerSide],
				[ProgramDeadlineDates].[date],[TimingCategory].*,
				[UniversalDeadlines].[name] AS [priorityName], [UniversalDeadlines].[ordering]
				FROM [ProgramTests]
				JOIN [SafetyTest] ON [SafetyTest].[id]=[ProgramTests].[safetyTestid]
				JOIN [ControlModelTestPairRequirements] ON [ControlModelTestPairRequirements].[programTestID]=[ProgramTests].[id]
				JOIN [ProgramDeadlineDates] ON [ControlModelTestPairRequirements].[deadlineID]=[ProgramDeadlineDates].[universalDeadlineID]
				JOIN [TimingCategory] ON [ControlModelTestPairRequirements].[timingCategoryID]=[TimingCategory].[id]
				JOIN [ControlModel] ON [ControlModel].[id]=[ControlModelTestPairRequirements].[controlModelID]
				JOIN [UniversalDeadlines] ON [UniversalDeadlines].[id]=[ControlModelTestPairRequirements].[deadlineid]
				WHERE [ProgramTests].[programID]=%d AND [ProgramDeadlineDates].[Programid]=%d
	"""

    cursor.execute(sql, (program_id, program_id))

    for r in cursor:
        test_id = r["testID"]
        control_model_id = r["controlModelID"]
        priority_name = r["priorityName"]
        deadline_id = r["deadlineID"]
        due_date = r["date"]

        prep = r["prep"]
        prep_rehit = r["prepRehit"]
        rework = r["rework"]
        rework_rehit = r["reworkRehit"]
        parts = r["parts"]
        vev = r["vev"]
        non_vev = r["nonVev"]
        tat = r["tat"]
        analysis = r["analysis"]

        req_witness = r["req_witness"]

        safety_id = r["safetyID"]
        max_speed = r["max_kph"]

        driver_side = r["driverSide"]
        filler_side = r["fillerSide"]
        relative_position_id = r["positionID"]
        abs_position_id = position(relative_position_id, driver_side, filler_side)
        if abs_position_id==LEFT:
            position = "LEFT"
        elif abs_position_id==RIGHT:
            position = "RIGHT"
        elif abs_position_id==DRIVER_SIDE:
            position = "DRIVER_SIDE"
        elif abs_position_id==PASSENGER_SIDE:
            position = "PASSENGER_SIDE"
        elif abs_position_id==FUEL_FILLER:
            position = "FUEL_FILLER_SIDE"
        elif abs_position_id==OPPOSITE_FUEL_FILLER:
            position = "OPPO_FILLER_SIDE"
        else:
            position = None

    cursor.close()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print "Need to provide a program id"
    else:
        program_id = int(sys.argv[1])
        print get_safetymode_info()
