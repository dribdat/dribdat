from pyomo.environ import *
import logging
import os
from .utils import unpack_csvlist

def get_matching_results(users, projects, pre_made_teams=None):
    """
    Main entry point for the matching algorithm.
    :param users: List of User model objects.
    :param projects: List of Project model objects.
    :param pre_made_teams: Dictionary mapping team_id to list of user usernames.
    :return: List of matches (user, project).
    """
    # 1. Prepare Data
    user_ids = [u.id for u in users]
    project_ids = [p.id for p in projects]

    # Map user/project IDs to objects for easy retrieval
    user_map = {u.id: u for u in users}
    project_map = {p.id: p for p in projects}

    # Project capacities
    default_cap = int(os.environ.get('DRIBDAT_TEAM_SIZE', 5))
    caps = {p.id: default_cap for p in projects}

    # Project skill requirements
    # reqs[project_id] = list of required skills
    reqs = {}
    all_skills = set()
    for p in projects:
        # technai is a list if coming from our Mock, but a CSV string if from the DB
        p_skills = p.technai
        if isinstance(p_skills, str):
            p_skills = unpack_csvlist(p_skills)
        reqs[p.id] = p_skills
        all_skills.update(p_skills)

    # User skills
    # user_skills[user_id] = list of user skills
    user_skills = {}
    for u in users:
        u_s = u.my_skills
        if isinstance(u_s, str):
            u_s = unpack_csvlist(u_s)
        user_skills[u.id] = u_s

    # User Preferences (Weights)
    # weights[user_id, project_id] = score (lower is better)
    weights = {}
    for u in users:
        ranking = u.my_ranking
        if isinstance(ranking, str):
            ranking = unpack_csvlist(ranking)

        for p_id in project_ids:
            try:
                if ranking and str(p_id) in ranking:
                    weights[u.id, p_id] = ranking.index(str(p_id)) + 1
                else:
                    weights[u.id, p_id] = 10
            except ValueError:
                weights[u.id, p_id] = 10

    # Pre-assigned matches (pre-made teams)
    pre_assigned = {}
    for u in users:
        starred_projects = [p for p in u.joined_projects() if p.id in project_ids]
        if starred_projects:
            pre_assigned[u.id] = starred_projects[0].id

    # 2. Build Pyomo Model
    model = ConcreteModel()

    # Decision variables: x[i, j] = 1 if user i is matched to project j
    model.x = Var(user_ids, project_ids, domain=Binary)

    # Imbalance variable: z (to minimize difference between team sizes)
    model.z = Var(domain=NonNegativeReals)

    # Objective: Minimize total weights + small penalty for imbalance
    model.obj = Objective(
        expr = sum(model.x[i, j] * weights[i, j] for i in user_ids for j in project_ids) + 0.01 * model.z,
        sense = minimize
    )

    # Constraints

    # 1. Each user must be assigned to exactly one project
    def one_project_rule(model, i):
        return sum(model.x[i, j] for j in project_ids) == 1
    model.one_project_per_user = Constraint(user_ids, rule=one_project_rule)

    # 2. Project capacity
    def capacity_rule(model, j):
        return sum(model.x[i, j] for i in user_ids) <= caps[j]
    model.project_capacity = Constraint(project_ids, rule=capacity_rule)

    # 3. Skill requirements
    def skill_rule(model, j, k):
        required_count = reqs[j].count(k)
        if required_count > 0:
            matching_users = [i for i in user_ids if k in user_skills[i]]
            if not matching_users:
                # If no one has this skill, we can't satisfy the constraint.
                # In Pyomo, returning False or 0 >= 1 would cause an error during construction.
                # Let's return Infeasible or an impossible constraint.
                return sum(model.x[i, j] for i in user_ids) >= required_count # Impossible if k in user_skills[i] is empty
            return sum(model.x[i, j] for i in matching_users) >= required_count
        return Constraint.Skip

    model.skill_requirements = Constraint(project_ids, all_skills, rule=skill_rule)

    # 4. Minimize imbalance
    def imbalance_rule(model, j1, j2):
        if j1 == j2: return Constraint.Skip
        return sum(model.x[i, j1] for i in user_ids) - sum(model.x[i, j2] for i in user_ids) <= model.z
    model.imbalance = Constraint(project_ids, project_ids, rule=imbalance_rule)

    # 5. Pre-assigned matches
    def pre_assigned_rule(model, i):
        if i in pre_assigned:
            return model.x[i, pre_assigned[i]] == 1
        return Constraint.Skip
    model.pre_assigned_constraint = Constraint(user_ids, rule=pre_assigned_rule)

    # 3. Solve
    solver = SolverFactory('appsi_highs')
    if not solver.available():
         logging.error("HiGHS solver not found.")
         return None

    results = solver.solve(model)

    if results.solver.status != SolverStatus.ok:
        logging.warning("No optimal solution found.")
        return None

    # 4. Extract Results
    matches = []
    for i in user_ids:
        for j in project_ids:
            if value(model.x[i, j]) > 0.5:
                matches.append({
                    'user': user_map[i],
                    'project': project_map[j]
                })

    return matches
