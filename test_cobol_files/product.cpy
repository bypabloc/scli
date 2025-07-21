      * PRODUCT RECORD COPYBOOK
       01  PRODUCT-RECORD.
           05  PRODUCT-ID          PIC 9(8).
           05  PRODUCT-NAME        PIC X(40).
           05  PRODUCT-CATEGORY    PIC X(15).
           05  UNIT-PRICE          PIC 9(5)V99.
           05  QUANTITY-ON-HAND    PIC 9(6).
           05  REORDER-LEVEL       PIC 9(4).
           05  SUPPLIER-ID         PIC 9(6).
           05  PRODUCT-STATUS      PIC X(1).
               88  ACTIVE-PRODUCT  VALUE 'A'.
               88  DISCONTINUED    VALUE 'D'.
           05  LAST-ORDERED-DATE   PIC 9(8).