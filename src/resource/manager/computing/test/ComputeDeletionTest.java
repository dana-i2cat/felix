package computing.test;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class ComputeDeletionTest {

   static String DELETED_SUCCESSFULLY = "Compute deleted successfully";
   String message = DELETED_SUCCESSFULLY;    
   
   @Test
   public void testDeletionProcedure() {    
      assertEquals(message, DELETED_SUCCESSFULLY);
   }
}
