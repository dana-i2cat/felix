package computing.test;

import static org.junit.Assert.assertEquals;
import org.junit.Ignore;
import org.junit.Test;

public class ComputeCreationTest {

   String message = "Compute created successfully";	
   
   @Test
   public void testCreationProcedure() {	
      assertEquals(message, "Compute created successfully");     
   }
}
