package computing.test;

import org.junit.runner.RunWith;
import org.junit.runners.Suite;

import computing.test.ComputeCreationTest;

//JUnit Suite Test
@RunWith(Suite.class)
@Suite.SuiteClasses({ComputeCreationTest.class, ComputeDeletionTest.class})
public class ComputeSuiteTest {
}
