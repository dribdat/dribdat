# -*- coding: utf-8 -*-
import unittest
from dribdat.matching import get_matching_results
from collections import namedtuple

# Mocking the User and Project models for testing
UserMock = namedtuple('User', ['id', 'username', 'my_ranking', 'my_skills', 'joined_projects'])
ProjectMock = namedtuple('Project', ['id', 'name', 'technai'])

class TestMatching(unittest.TestCase):

    def test_basic_matching(self):
        """Test a simple matching with 2 users and 2 projects."""
        p1 = ProjectMock(id=1, name="Project 1", technai=[])
        p2 = ProjectMock(id=2, name="Project 2", technai=[])

        # User 1 prefers Project 1
        u1 = UserMock(id=10, username="user1", my_ranking=['1', '2'], my_skills=[], joined_projects=lambda: [])
        # User 2 prefers Project 2
        u2 = UserMock(id=11, username="user2", my_ranking=['2', '1'], my_skills=[], joined_projects=lambda: [])

        matches = get_matching_results([u1, u2], [p1, p2])

        self.assertIsNotNone(matches)
        self.assertEqual(len(matches), 2)

        match_dict = {m['user'].id: m['project'].id for m in matches}
        self.assertEqual(match_dict[10], 1)
        self.assertEqual(match_dict[11], 2)

    def test_string_parsing(self):
        """Test that CSV string inputs are correctly parsed."""
        # Use comma-separated strings as in the real Dribdat database
        p1 = ProjectMock(id=1, name="Project 1", technai="python,data")
        p2 = ProjectMock(id=2, name="Project 2", technai="")

        # User 1 has skills as a string and prefers Project 2
        u1 = UserMock(id=10, username="user1", my_ranking="2,1", my_skills="python", joined_projects=lambda: [])
        # User 2 prefers Project 2
        u2 = UserMock(id=11, username="user2", my_ranking="2", my_skills="", joined_projects=lambda: [])

        matches = get_matching_results([u1, u2], [p1, p2])

        self.assertIsNotNone(matches)
        self.assertEqual(len(matches), 2)

        match_dict = {m['user'].id: m['project'].id for m in matches}
        self.assertEqual(match_dict[10], 1)
        self.assertEqual(match_dict[11], 2)

    def test_capacity_constraint(self):
        """Test that capacity constraints are respected."""
        import os
        os.environ['DRIBDAT_TEAM_SIZE'] = '1'

        p1 = ProjectMock(id=1, name="Project 1", technai=[])
        p2 = ProjectMock(id=2, name="Project 2", technai=[])

        # Both users prefer Project 1, but capacity is 1
        u1 = UserMock(id=10, username="user1", my_ranking=['1'], my_skills=[], joined_projects=lambda: [])
        u2 = UserMock(id=11, username="user2", my_ranking=['1'], my_skills=[], joined_projects=lambda: [])

        matches = get_matching_results([u1, u2], [p1, p2])

        self.assertIsNotNone(matches)
        match_dict = {m['user'].id: m['project'].id for m in matches}

        # One should be in p1, the other in p2
        self.assertIn(match_dict[10], [1, 2])
        self.assertIn(match_dict[11], [1, 2])
        self.assertNotEqual(match_dict[10], match_dict[11])

    def test_skill_requirements(self):
        """Test that skill requirements are respected."""
        # Project 1 requires 'python'
        p1 = ProjectMock(id=1, name="Project 1", technai=['python'])
        p2 = ProjectMock(id=2, name="Project 2", technai=[])

        # User 1 has 'python' but prefers Project 2
        u1 = UserMock(id=10, username="user1", my_ranking=['2', '1'], my_skills=['python'], joined_projects=lambda: [])
        # User 2 has no skills and prefers Project 2
        u2 = UserMock(id=11, username="user2", my_ranking=['2', '1'], my_skills=[], joined_projects=lambda: [])

        matches = get_matching_results([u1, u2], [p1, p2])

        self.assertIsNotNone(matches)
        match_dict = {m['user'].id: m['project'].id for m in matches}

        # User 1 MUST be in Project 1 because they are the only one with the required skill
        self.assertEqual(match_dict[10], 1)
        self.assertEqual(match_dict[11], 2)

    def test_pre_made_teams(self):
        """Test that users already in a project stay there."""
        p1 = ProjectMock(id=1, name="Project 1", technai=[])
        p2 = ProjectMock(id=2, name="Project 2", technai=[])

        # User 1 prefers Project 2 but has already joined Project 1
        u1 = UserMock(id=10, username="user1", my_ranking=['2', '1'], my_skills=[], joined_projects=lambda: [p1])
        u2 = UserMock(id=11, username="user2", my_ranking=['2', '1'], my_skills=[], joined_projects=lambda: [])

        matches = get_matching_results([u1, u2], [p1, p2])

        self.assertIsNotNone(matches)
        match_dict = {m['user'].id: m['project'].id for m in matches}

        self.assertEqual(match_dict[10], 1)
        self.assertEqual(match_dict[11], 2)

if __name__ == '__main__':
    unittest.main()
