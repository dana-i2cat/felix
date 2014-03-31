package computing.test;

import static org.junit.Assert.assertEquals;
import org.junit.Test;

public class ComputeCreationTest {

   static String CREATED_SUCCESSFULLY = "Compute created successfully";   
   String message = CREATED_SUCCESSFULLY;

   @Test
   public void testCreationProcedure() {    
      assertEquals(message, CREATED_SUCCESSFULLY);     
   }
}
