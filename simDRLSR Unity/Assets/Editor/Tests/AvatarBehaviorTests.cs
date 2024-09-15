using UnityEngine;
using UnityEngine.TestTools;
using NUnit.Framework;
using System.Collections;
using System.IO;
using Newtonsoft.Json;
using System.Collections.Generic;
using static AvatarBehaviors;

namespace Editor.Tests
{
    public class MockConfigureSimulation : ConfigureSimulation
    {
        public override void InitializeForTesting()
        {
            base.InitializeForTesting();
        }
    }
    
    public class AvatarBehaviorTests
    {
        private AvatarBehaviors avatarBehaviors;
        private MockConfigureSimulation configureSimulation;

        [SetUp]
        public void SetUp()
        {
            GameObject testObject = new GameObject();
            avatarBehaviors = testObject.AddComponent<AvatarBehaviors>();
            configureSimulation = testObject.AddComponent<MockConfigureSimulation>();
            configureSimulation.InitializeForTesting();
        }

        [Test]
        public void TestProbabilityFileLoading()
        {
            string configPath = configureSimulation.getPathConfig();
            string filePath = Path.Combine(configPath, "engaged_hri_probabilities.json");

            Assert.IsTrue(File.Exists(filePath), "Probability file does not exist");

            string jsonContent = File.ReadAllText(filePath);
            var probabilityData = JsonConvert.DeserializeObject<RootObject>(jsonContent);

            Assert.IsNotNull(probabilityData, "Failed to parse JSON content");
            Assert.IsTrue(probabilityData.probabilities.Count > 0, "No probability data found in JSON");
        }

        [Test]
        public void TestProbabilitySumToHundred()
        {
            string configPath = configureSimulation.getPathConfig();
            string filePath = Path.Combine(configPath, "engaged_hri_probabilities.json");
            string jsonContent = File.ReadAllText(filePath);
            var probabilityData = JsonConvert.DeserializeObject<RootObject>(jsonContent);

            foreach (var prob in probabilityData.probabilities)
            {
                int sum = 0;
                foreach (var value in prob.probabilities.Values)
                {
                    sum += value;
                }

                Assert.AreEqual(100, sum, $"Probabilities for {prob.interaction_type} do not sum to 100");
            }
        }

        [Test]
        public void TestGetHumanActionByProb()
        {
            var probTab = avatarBehaviors.initProbabilities(Path.Combine(configureSimulation.getPathConfig(),
                "engaged_hri_probabilities.json"));

            // Test for WaitClose interaction type
            var actionCounts = new Dictionary<HumanActionType, int>();
            int totalTrials = 10000;

            for (int i = 0; i < totalTrials; i++)
            {
                HumanActionType action = avatarBehaviors.getHumanActionByProb(probTab, InteractionType.WaitClose);
                if (!actionCounts.ContainsKey(action))
                {
                    actionCounts[action] = 0;
                }

                actionCounts[action]++;
            }

            // Check if the distribution matches the expected probabilities
            Assert.That(actionCounts[HumanActionType.Ignore], Is.InRange(1800, 2200)); // Expected 20%
            Assert.That(actionCounts[HumanActionType.Wait], Is.InRange(7800, 8200)); // Expected 80%
        }

        [Test]
        public void TestAlternativeProbabilityFile()
        {
            string alternativeFilePath =
                Path.Combine(configureSimulation.getPathConfig(), "alternative_probabilities.json");

            // Create an alternative probability file for testing
            var alternativeProbabilities = new RootObject
            {
                probabilities = new List<ProbabilityData>
                {
                    new ProbabilityData
                    {
                        interaction_type = "WaitClose",
                        probabilities = new Dictionary<string, int>
                        {
                            { "Ignore", 50 },
                            { "Wait", 50 },
                            { "Look", 0 },
                            { "Move", 0 },
                            { "Handshake", 0 }
                        }
                    }
                    // Add more interaction types as needed
                }
            };

            string json = JsonConvert.SerializeObject(alternativeProbabilities, Formatting.Indented);
            File.WriteAllText(alternativeFilePath, json);

            // Test loading and using the alternative file
            var altProbTab = avatarBehaviors.initProbabilities(alternativeFilePath);

            var actionCounts = new Dictionary<HumanActionType, int>();
            int totalTrials = 10000;

            for (int i = 0; i < totalTrials; i++)
            {
                HumanActionType action = avatarBehaviors.getHumanActionByProb(altProbTab, InteractionType.WaitClose);
                if (!actionCounts.ContainsKey(action))
                {
                    actionCounts[action] = 0;
                }

                actionCounts[action]++;
            }

            // Check if the distribution matches the alternative probabilities
            Assert.That(actionCounts[HumanActionType.Ignore], Is.InRange(4800, 5200)); // Expected 50%
            Assert.That(actionCounts[HumanActionType.Wait], Is.InRange(4800, 5200)); // Expected 50%
        }

        [Test]
        public void TestJsonFileFormat()
        {
            string configPath = configureSimulation.getPathConfig();
            string filePath = Path.Combine(configPath, "engaged_hri_probabilities.json");

            Assert.IsTrue(File.Exists(filePath), "Probability file does not exist");

            string jsonContent = File.ReadAllText(filePath);
            var probabilityData = JsonConvert.DeserializeObject<RootObject>(jsonContent);

            Assert.IsNotNull(probabilityData, "Failed to parse JSON content");
            Assert.IsNotNull(probabilityData.probabilities, "Probabilities list is null");
            Assert.IsTrue(probabilityData.probabilities.Count > 0, "No probability data found in JSON");

            var expectedInteractionTypes = new HashSet<string>
            {
                "WaitClose", "WaitMiddle", "WaitFar",
                "LookClose", "LookMiddle", "LookFar",
                "WaveClose", "WaveMiddle", "WaveFar",
                "HSClose", "HSMiddle", "HSFar"
            };

            var expectedActionTypes = new HashSet<string>
            {
                "Ignore", "Wait", "Look", "Move", "Handshake"
            };

            foreach (var prob in probabilityData.probabilities)
            {
                Assert.IsTrue(expectedInteractionTypes.Contains(prob.interaction_type),
                    $"Unexpected interaction type: {prob.interaction_type}");

                Assert.IsNotNull(prob.probabilities, $"Probabilities for {prob.interaction_type} is null");

                foreach (var action in prob.probabilities.Keys)
                {
                    Assert.IsTrue(expectedActionTypes.Contains(action),
                        $"Unexpected action type for {prob.interaction_type}: {action}");
                }

                foreach (var actionType in expectedActionTypes)
                {
                    Assert.IsTrue(prob.probabilities.ContainsKey(actionType),
                        $"Missing action type for {prob.interaction_type}: {actionType}");
                }

                int sum = 0;
                foreach (var value in prob.probabilities.Values)
                {
                    Assert.IsTrue(value >= 0 && value <= 100,
                        $"Invalid probability value for {prob.interaction_type}: {value}");
                    sum += value;
                }

                Assert.AreEqual(100, sum,
                    $"Probabilities for {prob.interaction_type} do not sum to 100");
            }
        }

        [TearDown]
        public void TearDown()
        {
            // Clean up
            Object.DestroyImmediate(avatarBehaviors.gameObject);
        }
    }
}