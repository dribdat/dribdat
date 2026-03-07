# Matching Algorithm

Dribdat uses an optimization-based matching algorithm to help organizers form teams during hackathons. The algorithm is implemented using [Pyomo](https://www.pyomo.org/) and solved with the [HiGHS](https://highs.dev/) solver.

## How it works

The matching algorithm considers several factors to find an optimal assignment of participants to projects:

1.  **User Preferences:** Participants can rank projects they are interested in. The algorithm tries to assign each person to their highest-ranked project.
2.  **Project Capacities:** Each project has a maximum number of members it can accommodate (defaulting to the value of the `DRIBDAT_TEAM_SIZE` environment variable, or 5).
3.  **Skill Requirements:** Projects can specify required skills (using the `technai` field). The algorithm ensures that these requirements are met by assigning participants with the matching skills.
4.  **Team Imbalance:** The algorithm includes a small penalty for team size imbalance, encouraging teams of similar sizes.
5.  **Pre-made Teams:** If a participant has already "joined" (starred) a project in Dribdat, the algorithm treats this as a fixed assignment and keeps them in that project.

## Solver Configuration

The default solver is **HiGHS** (via the `highspy` package), which is an open-source high-performance solver for mixed-integer programming.

### Customization

-   **Team Size:** You can set the `DRIBDAT_TEAM_SIZE` environment variable to change the default capacity for all projects.
-   **Skill Matching:** Skills are matched between the `User.my_skills` and `Project.technai` fields.

## Development and Testing

The matching logic is located in `dribdat/matching.py`. You can run the dedicated matching tests using:

```bash
PYTHONPATH=. python tests/test_matching.py
```

For more information on optimization models and testing, refer to the [Pyomo documentation](https://pyomo.readthedocs.io/).
