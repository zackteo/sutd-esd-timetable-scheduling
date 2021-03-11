#!/usr/bin/env python3

import gurobipy as gp
from gurobipy import GRB

try:
    # Create a new model
    m = gp.Model("sutd_esd_timetable_scheduling")

    jobs, proc_time = gp.multidict(
        {
            "J01": [4],
            "J02": [4],
            "J03": [4],
            "J04": [4],
            "J05": [4],
            "J06": [4],
            "J07": [4],
            "J08": [4],
            "J09": [4],
            "J10": [4],
            "J11": [4],
            "J12": [4],
            "J13": [4],
            "J14": [2],
            "J15": [4],
            "J16": [4],
            "J17": [4],
            "J18": [4],
            "J19": [4],
            "J20": [4],
            "J21": [2],
            "J22": [4],
            "J23": [4],
            "J24": [4],
            "J25": [4],
            "J26": [4],
            "J27": [4],
            "J28": [2],
            "J29": [2],
            "J30": [4],
            "J31": [3],
            "J32": [3],
            "J33": [4],
            "J34": [4],
            # "J35": [4],
            "J36": [3],
            "J37": [3],
            "J38": [4],
        }
    )

    # weights based on starting time of a class
    old_weight = [
        2,
        1,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
    ]

    weight = [
        2,
        1,
        0,
        0,
        1,
        1,
        5,
        5,
        5,
        5,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
        7,
        7,
        8,
    ]

    T = 23  # 0.5h blocks per day 8.30 and 19.30
    Days = 5  # monday to friday

    # Create supporting variable indicating if job is running in a timeslot
    timeslot_taken = {(j, t, d): 0 for j in jobs for t in range(T) for d in range(Days)}

    # Create (start-)time indexed decision variables Xjtd
    X = m.addVars(timeslot_taken.keys(), vtype=GRB.BINARY, name="X")

    # Calculate value of the supporting variable
    for j in jobs:
        for t in range(T):
            minT = max(0, t + 1 - proc_time[j])
            maxT = t
            for d in range(Days):
                for s in range(minT, maxT + 1):
                    timeslot_taken[j, t, d] += X[j, s, d]

    jobs_in_timeslot = {(t, d): 0 for t in range(T) for d in range(Days)}

    Y = m.addVars(jobs_in_timeslot.keys(), vtype=GRB.CONTINUOUS, name="Y")

    # Set of Term 7 jobs we want to avoid clashing
    term_7 = [
        "J14",
        "J15",
        "J16",
        "J17",
        "J18",
        "J19",
        "J20",
        "J21",
        "J22",
        "J23",
        "J24",
        "J25",
        "J26",
        "J27",
    ]

    for t in range(T):
        for d in range(Days):
            for j in term_7:
                jobs_in_timeslot[t, d] += timeslot_taken[j, t, d]
            m.addConstr(Y[t, d] >= jobs_in_timeslot[t, d] - 1)
            m.addConstr(Y[t, d] >= 0)

    # Set objective function
    obj_func = gp.quicksum(
        weight[t] * X[j, t, d] for j in jobs for t in range(T) for d in range(Days)
    )

    new_obj_func = obj_func + gp.quicksum(
        Y[t, d] for t in range(T) for d in range(Days)
    )

    m.setObjective(new_obj_func, GRB.MINIMIZE)

    # Hardcode non-ESD classes
    m.addConstr(X["J28", 1, 3] == 1)
    m.addConstr(X["J29", 4, 0] == 1)
    m.addConstr(X["J30", 11, 0] == 1)
    m.addConstr(X["J31", 6, 0] == 1)
    m.addConstr(X["J32", 16, 1] == 1)
    m.addConstr(X["J33", 15, 0] == 1)
    m.addConstr(X["J34", 0, 4] == 1)
    # this should be week 14 only, conflicts with "J31"
    # m.addConstr(X["J35", 7, 0] == 1)
    m.addConstr(X["J36", 1, 0] == 1)
    m.addConstr(X["J37", 13, 1] == 1)
    m.addConstr(X["J38", 9, 1] == 1)

    timeslot_taken_plusone = {
        (j, t, d): 0 for j in jobs for t in range(T) for d in range(Days)
    }

    # Calculate value of the supporting variable
    for j in jobs:
        for t in range(T):
            minT = max(0, t + 1 - proc_time[j])
            maxT = min(t + 1, T - 1)
            for d in range(Days):
                for s in range(minT, maxT + 1):
                    timeslot_taken_plusone[j, t, d] += X[j, s, d]

    # Set of jobs using the same location
    locations = [
        ["J14", "J36", "J37", "J38"],
        ["J17", "J18"],
        ["J21", "J24", "J25"],
        ["J22", "J23", "J26", "J27"],
        ["J19", "J20"],
        [
            "J01",
            "J02",
            "J06",
            "J07",
            "J28",
            "J29",
            "J30",
            "J31",
            "J32",
            "J33",
            "J34",
            # "J35",
        ],
        ["J03", "J04", "J10", "J11", "J12", "J13", "J15", "J16"],
        ["J05", "J08", "J09"],
    ]

    # Jobs from a set of exclusive jobs J due to being the same location, cannot be started on the same day at the same time
    for location in locations:
        for d in range(Days):
            for t in range(T):
                same_day_time_location = 0
                for job in location:
                    same_day_time_location += timeslot_taken[job, t, d]
                m.addConstr(same_day_time_location <= 1)

    # Set of jobs with the same professor
    professors = [
        ["J01", "J02", "J03", "J04"],
        ["J05", "J06", "J07", "J08", "J09"],
        ["J10", "J11", "J12", "J13"],
        ["J14", "J15", "J16", "J17", "J18"],
        ["J19", "J20"],
        ["J21", "J22", "J23"],
        ["J24", "J25"],
        ["J26", "J27"],
    ]

    # Jobs from a set of exclusive jobs J due to being the same prof, cannot be started on the same day at the same time
    for professor in professors:
        for d in range(Days):
            for t in range(T):
                same_day_time_prof = 0
                for job in professor:
                    same_day_time_prof += timeslot_taken_plusone[job, t, d]
                m.addConstr(same_day_time_prof <= 1)

    class_subjects = [
        ["J01", "J02", "J05", "J06", "J07", "J10", "J11"],
        ["J03", "J04", "J05", "J08", "J09", "J12", "J13"],
        # Tracks?
        ["J19", "J20", "J26", "J27"],
        ["J14", "J15", "J16", "J17", "J18", "J21", "J22", "J23"],
    ]

    # Jobs from a set of exclusive jobs J due to being for the same class/track, cannot be started on the same day at the same time
    for c_subject in class_subjects:
        for d in range(Days):
            for t in range(T):
                same_day_time_class = 0
                for job in c_subject:
                    same_day_time_class += timeslot_taken_plusone[job, t, d]
                m.addConstr(same_day_time_class <= 1)

    # Each job j starts at exactly one time instant
    for j in jobs:
        job_start_once = 0
        for t in range(T):
            for d in range(Days):
                job_start_once += X[j, t, d]
        m.addConstr(job_start_once == 1)

    # All jobs cannot be processed at time instants corresponding to Wed/Fri afternoons
    job_on_wed_fri = 0
    for j in jobs:
        for d in [2, 4]:
            for t in range(9, T):
                minT = max(0, t + 1 - proc_time[j])
                maxT = t
                for s in range(minT, maxT + 1):
                    job_on_wed_fri += X[j, s, d]
    m.addConstr(job_on_wed_fri == 0)

    ESD_jobs = [
        "J01",
        "J02",
        "J03",
        "J04",
        "J05",
        "J06",
        "J07",
        "J08",
        "J09",
        "J10",
        "J11",
        "J12",
        "J13",
        "J14",
        "J15",
        "J16",
        "J17",
        "J18",
        "J19",
        "J20",
        "J21",
        "J22",
        "J23",
        "J24",
        "J25",
        "J26",
        "J27",
    ]

    # All ESD jobs start 1830 latest, avoid ending past 2030
    for j in ESD_jobs:
        for d in range(Days):
            for t in range(21, T):
                m.addConstr(X[j, t, d] == 0)

    # create template function for time-instant constraints
    def time_instant_constraint(start, end, day):
        time_instant_sum = 0
        for j in ESD_jobs:
            for d in [day]:
                for t in range(start, end):  # could use refinement
                    minT = max(0, t + 1 - proc_time[j])
                    maxT = t
                    for s in range(minT, maxT + 1):
                        time_instant_sum += X[j, s, d]
        m.addConstr(time_instant_sum == 0)

    # All jobs cannot be processed at time instants corresponding to HASS/TAE blocks
    time_instant_constraint(13, 19, 0)
    time_instant_constraint(0, 9, 1)
    time_instant_constraint(13, 19, 3)
    time_instant_constraint(1, 5, 3)
    time_instant_constraint(4, 10, 4)

    subjects = [
        ["J01", "J02"],
        ["J03", "J04"],
        ["J05", "J06", "J07"],
        ["J05", "J08", "J09"],
        ["J10", "J11"],
        ["J12", "J13"],
        ["J14", "J15", "J16"],
        ["J14", "J17", "J18"],
        ["J19", "J20"],
        ["J21", "J22", "J23"],
        ["J24", "J25"],
        ["J26", "J27"],
    ]

    # Jobs from a set of eclusive jobs J due to being the same subject cannot be started on the same day
    for subject in subjects:
        for d in range(Days):
            same_day_subject = 0
            for s in subject:
                for t in range(T):
                    same_day_subject += X[s, t, d]
            m.addConstr(same_day_subject <= 1)

    m.optimize()

    # Format data to human-friendly output
    job_to_class = {
        "J01": "40.004 Statistics CS01 Period 1",
        "J02": "40.004 Statistics CS01 Period 2",
        "J03": "40.004 Statistics CS02 Period 1",
        "J04": "40.004 Statistics CS02 Period 2",
        "J05": "40.012 Manufacturing and Service Operations LS01",
        "J06": "40.012 Manufacturing and Service Operations CS01 Period 1",
        "J07": "40.012 Manufacturing and Service Operations CS01 Period 2",
        "J08": "40.012 Manufacturing and Service Operations CS02 Period 1",
        "J09": "40.012 Manufacturing and Service Operations CS02 Period 2",
        "J10": "40.014 Engineering Systems Architecture CS01 Period 1",
        "J11": "40.014 Engineering Systems Architecture CS01 Period 2",
        "J12": "40.014 Engineering Systems Architecture CS02 Period 1",
        "J13": "40.014 Engineering Systems Architecture CS02 Period 2",
        "J14": "40.319 Statistical and Machine Learning LS01 (Lecture)",
        "J15": "40.319 Statistical and Machine Learning CS01 Period 1",
        "J16": "40.319 Statistical and Machine Learning CS01 Period 2",
        "J17": "40.319 Statistical and Machine Learning CS02 Period 1",
        "J18": "40.319 Statistical and Machine Learning CS02 Period 2",
        "J19": "40.242 Derivative Pricing and Risk Management Period 1",
        "J20": "40.242 Derivative Pricing and Risk Management Period 2",
        "J21": "40.302 Advanced Topics in Optimisation#/40.305 Advanced Topics in Stochastic Modelling# Lesson 1",
        "J22": "40.302 Advanced Topics in Optimisation#/40.305 Advanced Topics in Stochastic Modelling# Lesson 2",
        "J23": "40.302 Advanced Topics in Optimisation#/40.305 Advanced Topics in Stochastic Modelling# Lesson 3",
        "J24": "40.321 Airport Systems Modelling and Simulation Period 1",
        "J25": "40.321 Airport Systems Modelling and Simulation Period 2",
        "J26": "40.323 Equity Valuation Period 1",
        "J27": "40.323 Equity Valuation Period 2",
        "J28": "",
        "J29": "",
        "J30": "",
        "J31": "",
        "J32": "",
        "J33": "",
        "J34": "",
        # "J35": "",
        "J36": "",
        "J37": "",
        "J38": "",
    }

    index_to_time = {
        "0": "0830",
        "1": "0900",
        "2": "0930",
        "3": "1000",
        "4": "1030",
        "5": "1100",
        "6": "1130",
        "7": "1200",
        "8": "1230",
        "9": "1300",
        "10": "1330",
        "11": "1400",
        "12": "1430",
        "13": "1500",
        "14": "1530",
        "15": "1600",
        "16": "1630",
        "17": "1700",
        "18": "1730",
        "19": "1800",
        "20": "1830",
        "21": "1900",
        "22": "1930",
        "23": "2000",
        "24": "2030",
        "25": "2100",
        "26": "2130",
        "27": "2200",
        "28": "2230",
    }

    index_to_day = {
        "0": "Mon",
        "1": "Tue",
        "2": "Wed",
        "3": "Thu",
        "4": "Fri",
    }

    for x in X.values():
        if x.x > 0.5:
            day_index = x.varName[-2]
            start_time_index = (x.varName[6] + x.varName[7]).replace(",", "")
            subject_index = x.varName[2] + x.varName[3] + x.varName[4]
            print(
                "%s | %s | %s | %s"
                % (
                    index_to_day[day_index],
                    index_to_time[start_time_index],
                    index_to_time[
                        str(int(start_time_index) + proc_time[subject_index])
                    ],
                    job_to_class[subject_index],
                )
            )
    print("Obj: %g" % m.objVal)

except gp.GurobiError as e:
    print("Error code " + str(e.errno) + ": " + str(e))

except AttributeError:
    print("Encountered an attribute error")
