;; SWL loads this file in its REPL thread.
(load-shared-object "libc.so.6")
(define batch-exit (foreign-procedure "exit" (int) void))

(define (batch-json-string value)
  (if value
      (call-with-string-output-port
        (lambda (port)
          (put-char port #\")
          (string-for-each
            (lambda (ch)
              (cond
                ((or (char=? ch #\") (char=? ch #\\))
                 (put-char port #\\)
                 (put-char port ch))
                ((< (char->integer ch) 32)
                 (let ((digits (number->string (char->integer ch) 16)))
                   (display "\\u00" port)
                   (when (= (string-length digits) 1) (put-char port #\0))
                   (display digits port)))
                (else (put-char port ch))))
            value)
          (put-char port #\")))
      "null"))

(define (batch-condition-message condition)
  (call-with-string-output-port
    (lambda (port) (display-condition condition port))))

(define (batch-temperature temperature)
  (cond ((not temperature) "null")
        ((integer? temperature) (exact temperature))
        (else (inexact temperature))))

(define (write-batch-result report answer temperature codelets snags error-message)
  (fprintf report
    "{\"answer\":~a,\"final_temperature\":~a,\"codelets_run\":~a,\"snags\":~a,\"error\":~a}~%"
    (batch-json-string answer)
    (batch-temperature temperature)
    (or codelets "null")
    (or snags "null")
    (batch-json-string error-message))
  (flush-output-port report))

(define (batch-main report)
  (guard (condition
          (else
            (fprintf report "{\"error\":~a}~%"
              (batch-json-string (batch-condition-message condition)))
            (close-output-port report)
            (batch-exit 1)))
    (load "/opt/metacat-batch/original_metacat/metacat-linux.ss")
    (setup)
    (speed-slider-action #f 100)
    (call-with-input-file (getenv "METACAT_REQUESTS")
      (lambda (requests)
        (display "{\"ready\":true}" report)
        (put-char report #\newline)
        (flush-output-port report)
        (let loop ((trial (read requests)))
          (unless (eof-object? trial)
            (apply batch-trial report trial)
            (loop (read requests))))))
    (close-output-port report)
    ;; SWL's exit handler returns to the REPL. Exit the dedicated worker process.
    (batch-exit 0)))

(define (batch-trial report initial modified target seed limit)
  (let ((initialized? #f))
    (guard (condition
            (else
              (write-batch-result report #f
                (and initialized? *temperature*)
                (and initialized? *codelet-count*)
                #f
                (batch-condition-message condition))))
      (tell *memory* 'clear)
      (tell *control-panel* 'update-current-problem (list initial modified target seed))
      (tell *control-panel* 'switch-to-run-mode)
      (init-mcat initial modified target #f seed)
      (set! initialized? #t)
      (runtil limit)
      (call/cc
        (lambda (stopped)
          (parameterize ((reset-handler (lambda () (stopped #t))))
            (run-mcat))))
      (unless *breakpoint-continuation*
        (error 'batch-trial "Metacat reset outside its normal break handler"))
      (let* ((answers (tell *trace* 'get-events 'answer))
             ;; The trace keeps the newest events first.
             (answer (and (pair? answers) (car (reverse answers)))))
        (write-batch-result report
          (and answer (tell (tell answer 'get-answer-string) 'print-name))
          (if answer (tell answer 'get-temperature) *temperature*)
          ;; Answer and give-up stops occur inside the final codelet.
          (if (= *codelet-count* limit) limit (+ *codelet-count* 1))
          (tell *trace* 'get-num-of-events 'snag)
          #f)))))

(batch-main (open-output-file (getenv "METACAT_RESPONSES") 'truncate))
