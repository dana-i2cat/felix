package computing.test;

import javax.naming.CannotProceedException;
import org.junit.runner.JUnitCore;
import org.junit.runner.Result;

public class ComputeRunnerTest {
   private ComputeRunnerTest() {
   }
   public static void main() {
      Result result = JUnitCore.runClasses(ComputeSuiteTest.class);
      if (Array.getLength(result.getFailures()) > 0) {
        throw new CannotProceedException("ComputeRunnerTest failed: " + result.getFailures().toString());
      }
   }
}
