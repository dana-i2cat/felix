package computing.test;

import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;

import org.junit.runner.RunWith;
import org.junit.runners.Suite;

import computing.test.ComputeCreationTest;

//JUnit Suite Test
@RunWith(Suite.class)
@Suite.SuiteClasses({ComputeCreationTest.class, ComputeDeletionTest.class})
public class ComputeSuiteTest {
    public static void main(String[] args) {
    }
}
