+--------------------+       +---------------------+
|   Client (HR Admin)|       |   Shared Components |
|   POST /onboard    |       | common/models       |
|                    |       | common/httpclient   |
+--------------------+       +---------------------+
           |
           | HTTP
           v
+----------------------------------+
|         HR Service (8080)        |
|   +---------------------------+  |
|   | delivery/http/handler.go  |  |
|   | usecase/employee_usecase.go| |
|   | repository/mysql_repository| |
|   | http/orchestrator.go      |  |
|   +---------------------------+  |
|         MySQL: employees        |
+----------------------------------+
           |
           | HTTP Calls
           |
    +------+------+------+
    |             |      |
    v             v      v
+--------------------+  +--------------------+  +--------------------+
| IT Setup (8081)    |  | Email Prov (8082)  |  | Access Rights (8083)|
| +---------------+  |  | +---------------+  |  | +---------------+  |
| | handler.go    |  |  | | handler.go    |  |  | | handler.go    |  |
| | usecase.go    |  |  | | usecase.go    |  |  | | usecase.go    |  |
| | repository.go |  |  | | repository.go |  |  | | repository.go |  |
| +---------------+  |  | | mock_sender.go|  |  | +---------------+  |
| MySQL: it_provisions| | MySQL: email_logs |  | MySQL: access_grants|
+--------------------+  +--------------------+  +--------------------+