      * CUSTOMER RECORD COPYBOOK
       01  CUSTOMER-RECORD.
           05  CUSTOMER-ID         PIC 9(10).
           05  CUSTOMER-NAME       PIC X(30).
           05  CUSTOMER-ADDRESS.
               10  STREET          PIC X(25).
               10  CITY            PIC X(20).
               10  STATE           PIC X(2).
               10  ZIP-CODE        PIC 9(5).
           05  CUSTOMER-PHONE      PIC X(10).
           05  CUSTOMER-EMAIL      PIC X(50).
           05  ACCOUNT-BALANCE     PIC 9(7)V99.
           05  CUSTOMER-STATUS     PIC X(1).
               88  ACTIVE-CUSTOMER VALUE 'A'.
               88  INACTIVE-CUSTOMER VALUE 'I'.
           05  LAST-UPDATE-DATE    PIC 9(8).