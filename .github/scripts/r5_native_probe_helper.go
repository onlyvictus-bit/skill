// Probe-only helper: compile INSIDE the exact pinned Beads module.
package main

import (
 "context"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "regexp"
 "time"
 "github.com/steveyegge/beads/internal/storage/embeddeddolt"
 "github.com/steveyegge/beads/internal/storage/issueops"
 "github.com/steveyegge/beads/internal/storage/schema"
 "github.com/steveyegge/beads/internal/storage/versioncontrolops"
)
func main() { if err:=run();err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)} }
func run() error {
 if len(os.Args)!=8 {return fmt.Errorf("expected root, database, project, branch, operation, issue-or-new-branch, title")}
 root,db,project,branch,op,id,title:=os.Args[1],os.Args[2],os.Args[3],os.Args[4],os.Args[5],os.Args[6],os.Args[7]
 if !regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*$`).MatchString(db){return fmt.Errorf("database identifier refused")}
 if !filepath.IsAbs(root) {return fmt.Errorf("absolute disposable root required")}
 marker,err:=os.ReadFile(filepath.Join(root,"r5-disposable-probe.json"));if err!=nil{return err}
 var identity map[string]string;if err=json.Unmarshal(marker,&identity);err!=nil{return err}
 if identity["root"]!=root || identity["database"]!=db || identity["project"]!=project {return fmt.Errorf("disposable identity mismatch")}
 for _,p:=range []string{root,filepath.Join(root,".beads"),filepath.Join(root,".beads","metadata.json")} {s,e:=os.Lstat(p);if e!=nil{return e};if s.Mode()&os.ModeSymlink!=0{return fmt.Errorf("symlink refused")}}
 meta,err:=os.ReadFile(filepath.Join(root,".beads","metadata.json"));if err!=nil{return err};var m map[string]interface{};if err=json.Unmarshal(meta,&m);err!=nil{return err}
 if m["project_id"]!=project || m["dolt_database"]!=db || m["backend"]!="dolt" || m["dolt_mode"]!="embedded" {return fmt.Errorf("metadata mismatch")}
 if branch!="main" && !regexp.MustCompile(`^r5probe[a-z]+$`).MatchString(branch) {return fmt.Errorf("branch refused")}
 if op!="read" && op!="fork" && op!="write" {return fmt.Errorf("operation refused")}
 if op=="fork" && (branch!="main" || !regexp.MustCompile(`^r5probe[a-z]+$`).MatchString(id)) {return fmt.Errorf("fork refused")}
 if op=="write" && (branch=="main" || len(title)==0) {return fmt.Errorf("only source-branch title write permitted")}
 ctx,cancel:=context.WithTimeout(context.Background(),30*time.Second);defer cancel()
 // Beads store methods open new sessions. Keep checkout and every operation
 // on this one pinned connection. driver/v2 v2.2.0 discards pooled sessions,
 // so OpenSQL USE/head_ref setup must be reapplied after pinning.
 sqlDB,cleanup,err:=embeddeddolt.OpenSQL(ctx,filepath.Join(root,".beads","embeddeddolt"),db,"")
 if err!=nil{return err};defer cleanup()
 conn,err:=sqlDB.Conn(ctx);if err!=nil{return err};defer conn.Close()
 if _,err=conn.ExecContext(ctx,"USE `"+db+"`");err!=nil{return err}
 if err=versioncontrolops.CheckoutBranch(ctx,conn,branch);err!=nil{return err}
 defer func(){cleanupCtx,cancelCleanup:=context.WithTimeout(context.Background(),3*time.Second);defer cancelCleanup();_ = versioncontrolops.CheckoutBranch(cleanupCtx,conn,"main")}()
 selected,err:=versioncontrolops.CurrentBranch(ctx,conn);if err!=nil{return err};if selected!=branch{return fmt.Errorf("selected branch mismatch: %s",selected)}
 var before string;if err=conn.QueryRowContext(ctx,"SELECT HASHOF('HEAD')").Scan(&before);err!=nil{return err}
 var initializedHead string;var sourceLeaseCount int;var mainMigrationsApplied int
 if branch!="main" {
   mainMigrationsApplied,err=schema.MigrateUp(ctx,conn);if err!=nil{return fmt.Errorf("native source schema initialization: %w",err)}
   if err=conn.QueryRowContext(ctx,"SELECT HASHOF('HEAD')").Scan(&initializedHead);err!=nil{return err}
   if initializedHead!=before{return fmt.Errorf("native source initialization moved tracked head")}
   if err=conn.QueryRowContext(ctx,"SELECT COUNT(*) FROM leases").Scan(&sourceLeaseCount);err!=nil{return err}
   if sourceLeaseCount!=0{return fmt.Errorf("merge-only source branch contains unexpected leases")}
 }
 if op=="fork" {err=versioncontrolops.CreateBranch(ctx,conn,id)}
 if op=="write" {
   tx,e:=conn.BeginTx(ctx,nil);if e!=nil{return e}
   _,e=issueops.UpdateIssueInTx(ctx,tx,id,map[string]interface{}{"title":title},"r5branchprobe")
   if e!=nil{_ = tx.Rollback();return e};if e=tx.Commit();e!=nil{return e}
   status,e:=versioncontrolops.Status(ctx,conn);if e!=nil{return e};dirty:=map[string]bool{}
   for _,entry:=range status.Staged{dirty[entry.Table]=true};for _,entry:=range status.Unstaged{dirty[entry.Table]=true}
   if len(dirty)==0{return fmt.Errorf("source write produced no pending tracked tables")}
   err=versioncontrolops.StageAndCommit(ctx,conn,dirty,"R5 disposable source branch probe","")
 }
 if err!=nil{return err}
 var after string;if err=conn.QueryRowContext(ctx,"SELECT HASHOF('HEAD')").Scan(&after);err!=nil{return err}
 out:=map[string]interface{}{"branch":selected,"before_head":before,"head":after,"operation":op}
 if branch!="main"{out["native_initialized_head"]=initializedHead;out["source_lease_count"]=sourceLeaseCount;out["main_migrations_applied"]=mainMigrationsApplied}
 if op!="fork" {
   issue,e:=issueops.GetIssueInTx(ctx,conn,id);if e!=nil{return e};out["issue"]=issue
   log,e:=versioncontrolops.Log(ctx,conn,0);if e!=nil{return e};out["log"]=log
   conflicts,e:=versioncontrolops.GetConflicts(ctx,conn);if e!=nil{return e};out["conflicts"]=conflicts
 }
 if err=versioncontrolops.CheckoutBranch(ctx,conn,"main");err!=nil{return err}
 restored,err:=versioncontrolops.CurrentBranch(ctx,conn);if err!=nil{return err};if restored!="main"{return fmt.Errorf("main restoration failed")};out["restored_branch"]=restored
 return json.NewEncoder(os.Stdout).Encode(out)
}
