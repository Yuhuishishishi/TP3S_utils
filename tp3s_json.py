import argparse
import get_program_info
import get_rehit_lib
import json
import os.path
import os

DEFUALT_PATH = os.path.dirname(os.path.abspath(__file__))
DEFUALT_PATH = os.path.join(DEFUALT_PATH, "./output")


def test_json(program_id):
    print "Writing test info for program %d..." % program_id
    test_info = get_program_info.get_test_info(program_id)
    j = json.dumps({"tests":
                        test_info})
    if not os.path.exists(DEFUALT_PATH):
        os.makedirs(DEFUALT_PATH)
    file_path = os.path.join(DEFUALT_PATH, "test_%d.json" % program_id)
    print file_path
    with open(file_path, 'wb') as f:
        f.write(j)

    print "Done!"


def vehicle_json(program_id):
    print "Writing vehicle info for program %d..." % program_id

    vehicle_info = get_program_info.get_vehicle_info(program_id)
    j = json.dumps({
        "vehicles": vehicle_info
    })
    file_path = os.path.join(DEFUALT_PATH, "vehicle_%d.json" % program_id)
    with open(file_path, 'wb') as f:
        f.write(j)
    print "Done!"


def rehit_json(rehit_id):
    print "Writing rehit library info for rehit library %d..." % rehit_id

    rehit_lib_info = get_rehit_lib.get_json(rehit_id)
    j = rehit_lib_info
    file_path = os.path.join(DEFUALT_PATH, "rehit_lib_%d.json" % rehit_id)
    with open(file_path, 'wb') as f:
        f.write(j)
    print "Done!"


def milestone_json(program_id):
    print "Writing milestone info for program %d..." % program_id

    milestone_info = get_program_info.get_deadline_info(program_id)
    j = json.dumps({
        "milestones": milestone_info
    })
    file_path = os.path.join(DEFUALT_PATH, "milestone_%d.json" % program_id)
    with open(file_path, 'wb') as f:
        f.write(j)
    print "Done!"


def program_json(program_id):
    print "Writing program info for program %d..." % program_id

    program_info = get_program_info.get_program_info(program_id)
    j = json.dumps({
        "program": program_info
    })
    file_path = os.path.join(DEFUALT_PATH, "program_info_%d.json" % program_id)
    with open(file_path, 'wb') as f:
        f.write(j)
    print "Done!"


def comprehensive_json(run_id):
    print "Writing info for run config id %d" % run_id
    run_info = get_program_info.get_program_config(run_id)
    program_id = run_info["program_id"]
    rehit_lib_id = run_info["rehit_lib_id"]

    program_json(program_id)
    test_json(program_id)
    vehicle_json(program_id)
    milestone_json(program_id)

    rehit_json(rehit_lib_id)
    j = json.dumps(run_info)
    file_path = os.path.join(DEFUALT_PATH, "run_config_%d.json" % program_id)
    with open(file_path, 'wb') as f:
        f.write(j)
    print "Done!"




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="output the test info", type=int, metavar="PROGRAM_ID")
    parser.add_argument("-v", "--vehicle", help="output the vehicle info", type=int, metavar="PROGRAM_ID")
    parser.add_argument("-m", "--milestone", help="output the milestone info", type=int, metavar="PROGRAM_ID")
    parser.add_argument("-p", "--program", help="output the program info", type=int, metavar="PROGRAM_ID")
    parser.add_argument("-l", "--library", help="output the rehit library info", type=int, metavar="REHIT_LIB_ID")

    parser.add_argument("-r", "--runconfig", help="output all relevant information given run config id", type=int,
                        metavar="RUN_CONFIG_ID")
    parser.add_argument("-o", "--output", help="directory to store the output data")

    args = parser.parse_args()
    if args.test:
        program_id = args.test
        test_json(program_id)
    if args.vehicle:
        program_id = args.vehicle
        vehicle_json(program_id)
    if args.milestone:
        program_id = args.milestone
        milestone_json(program_id)
    if args.library:
        rehit_lib_id = args.library
        rehit_json(rehit_lib_id)
    if args.program:
        program_id = args.program
        program_json(program_id)
    if  args.runconfig:
        config_id = args.runconfig
        comprehensive_json(config_id)


if __name__ == '__main__':
    main()
