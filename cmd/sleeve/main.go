/*
Copyright 2021.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package main

import (

	// Import all Kubernetes client auth plugins (e.g. Azure, GCP, OIDC, etc.)
	// to ensure that exec-entrypoint and run can make use of them.

	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"sort"

	_ "k8s.io/client-go/plugin/pkg/client/auth"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	"github.com/samber/lo"
	sleevectrl "github.com/tgoodwin/sleeve/controller-manager/pkg/controller"
	"github.com/tgoodwin/sleeve/pkg/event"
	"github.com/tgoodwin/sleeve/pkg/tracecheck"
	"github.com/tgoodwin/sleeve/pkg/util"
	sleevelog "github.com/tgoodwin/sleeve/pkg/util/logger"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"
	"k8s.io/apimachinery/pkg/types"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"

	api "github.com/k8ssandra/cass-operator/apis/cassandra/v1beta1"
	configv1beta1 "github.com/k8ssandra/cass-operator/apis/config/v1beta1"
	controlv1alpha1 "github.com/k8ssandra/cass-operator/apis/control/v1alpha1"
	controllers "github.com/k8ssandra/cass-operator/internal/controllers/cassandra"
	"github.com/k8ssandra/cass-operator/pkg/images"
)

var (
	scheme   = runtime.NewScheme()
	setupLog = ctrl.Log.WithName("setup")
)

func init() {
	utilruntime.Must(clientgoscheme.AddToScheme(scheme))

	utilruntime.Must(api.AddToScheme(scheme))
	utilruntime.Must(configv1beta1.AddToScheme(scheme))
	utilruntime.Must(controlv1alpha1.AddToScheme(scheme))
}

func main() {
	logfile := flag.String("logfile", "app.log", "path to the log file")
	// stalenessDepth := flag.Int("staleness-depth", 1, "staleness depth")
	searchDepth := flag.Int("search-depth", 3, "search depth")
	outDir := flag.String("out-dir", "out", "output directory")

	var configFile string
	flag.StringVar(&configFile, "config", "",
		"The cass-operator will load its configuration from this file. "+
			"Omit this flag to use the default configuration values. ")
	flag.Parse()

	logger := sleevelog.GetLogger(sleevelog.Debug)
	// ctrl.SetLogger(logger)
	tracecheck.SetLogger(logger)

	operConfig := &configv1beta1.OperatorConfig{}
	if configFile != "" {
		var err error
		operConfig, err = readOperConfig(configFile)
		if err != nil {
			setupLog.Error(err, "unable to load the config file")
			os.Exit(1)
		}
	}

	if operConfig.ImageConfigFile == "" {
		operConfig.ImageConfigFile = "/configs/image_config.yaml"
	}

	err := images.ParseImageConfig(operConfig.ImageConfigFile)
	if err != nil {
		setupLog.Error(err, "unable to load the image config file")
		os.Exit(1)
	}

	// sleeve stuff
	eb := tracecheck.NewExplorerBuilder(scheme)
	traces, err := eb.ParseJSONLTrace(*logfile)
	if err != nil {
		log.Fatalf("failed to parse JSONL trace: %v", err)
	}
	log.Printf("Parsed %d trace events", len(traces))

	sort.Slice(traces, func(i, j int) bool {
		return traces[i].Timestamp < traces[j].Timestamp
	})

	byKind := lo.GroupBy(traces, func(t tracecheck.StateEvent) string {
		return t.Kind
	})
	for kind, traces := range byKind {
		log.Printf("Kind: %s, count: %d", kind, len(traces))
		byOpType := lo.GroupBy(traces, func(t tracecheck.StateEvent) string {
			return t.OpType
		})
		for opType, traces := range byOpType {
			log.Printf("  OpType: %s, count: %d", opType, len(traces))
		}
	}

	for _, trace := range traces {
		if !event.IsWriteOp(event.OperationType(trace.OpType)) {
			continue
		}
		fmt.Printf("Timestamp: %s, Kind: %s, ObjectID: %s, %s:%s\n", trace.Timestamp, trace.Kind, util.Shorter(trace.ObjectID), trace.ControllerID, trace.OpType)
	}

	eb.WithReconciler("CassandraDatacenter", func(c tracecheck.Client) tracecheck.Reconciler {
		return &controllers.CassandraDatacenterReconciler{
			Client: c,
			Scheme: scheme,
		}
	})

	eb.WithReconciler("StatefulSetController", func(c tracecheck.Client) tracecheck.Reconciler {
		return &sleevectrl.StatefulSetReconciler{
			Client: c,
			Scheme: scheme,
		}
	})

	eb.WithReconciler("ServiceController", func(c tracecheck.Client) tracecheck.Reconciler {
		return &sleevectrl.ServiceReconciler{
			Client: c,
			Scheme: scheme,
		}
	})

	eb.WithReconciler("PersistentVolumeClaimController", func(c tracecheck.Client) tracecheck.Reconciler {
		return &sleevectrl.PersistentVolumeClaimReconciler{
			Client: c,
			Scheme: scheme,
		}
	})

	eb.WithResourceDep("CassandraDatacenter", "CassandraDatacenter")
	eb.WithResourceDep("StatefulSet", "CassandraDatacenter")
	// eb.WithResourceDep("PodDisruptionBudget", "CassandraDatacenter")
	eb.WithResourceDep("Service", "CassandraDatacenter")
	// eb.WithResourceDep("Secret", "CassandraDatacenter")

	// eb.WithResourceDep("StatefulSet", "StatefulSetController")
	// eb.WithResourceDep("PersistentVolumeClaim", "StatefulSetController")
	// eb.WithResourceDep("Pod", "StatefulSetController")

	// eb.WithResourceDep("Service", "ServiceController")
	// eb.WithResourceDep("Endpoints", "ServiceController")
	// eb.WithResourceDep("Pod", "ServiceController")

	// eb.WithResourceDep("PersistentVolumeClaim", "PersistentVolumeClaimController")
	// eb.WithResourceDep("PersistentVolume", "PersistentVolumeClaimController")

	eb.AssignReconcilerToKind("CassandraDatacenter", "CassandraDatacenter")
	eb.AssignReconcilerToKind("StatefulSetController", "StatefulSet")
	eb.AssignReconcilerToKind("ServiceController", "Service")
	eb.AssignReconcilerToKind("PersistentVolumeClaimController", "PersistentVolumeClaim")

	emitter := event.NewDebugEmitter()
	eb.WithEmitter(emitter)
	// eb.WithStalenessDepth(*stalenessDepth) // Enable staleness exploration
	eb.WithMaxDepth(*searchDepth) // tuned this experimentally
	// eb.WithKindBounds("CassandraDatacenter", tracecheck.ReconcilerConfig{
	// 	Bounds:      tracecheck.LookbackLimits{"CassandraDatacenter": 10},
	// 	MaxRestarts: 1,
	// })

	explorer, err := eb.Build("standalone")
	if err != nil {
		log.Fatalf("failed to build explorer: %v", err)
	}

	rollup := tracecheck.Rollup(traces)
	rollup.Debug()

	fmt.Println("stale view")
	fixed := rollup.FixAt(tracecheck.KindSequences{
		"CassandraDatacenter": 40,
	})
	fixed.Debug()

	topState := tracecheck.StateNode{
		Contents: fixed,
		PendingReconciles: []tracecheck.PendingReconcile{
			{
				ReconcilerID: "CassandraDatacenter",
				Request: reconcile.Request{
					NamespacedName: types.NamespacedName{
						Name:      "sample-dc",
						Namespace: "tracey",
					},
				},
			},
		},
	}

	result := explorer.Explore(context.Background(), topState)
	fmt.Println("Number of converged states: ", len(result.ConvergedStates))

	classifier := eb.NewStateClassifier()
	predicateBuilder := classifier.NewPredicateBuilder()
	pred := predicateBuilder.And(
		predicateBuilder.ObjectsCountOfKind("CassandraDatacenter", 1),
		predicateBuilder.ObjectsCountOfKind("PersistentVolumeClaim", 3),
	)

	classified := classifier.ClassifyResults(result.ConvergedStates, pred)
	happy := lo.Filter(classified, func(s tracecheck.ClassifiedState, _ int) bool {
		return s.Classification == "happy"
	})
	sad := lo.Filter(classified, func(s tracecheck.ClassifiedState, _ int) bool {
		return s.Classification == "bad"
	})
	fmt.Println("number of happy states: ", len(happy))
	fmt.Println("number of sad states: ", len(sad))

	resultWriter := tracecheck.NewResultWriter(emitter)
	resultWriter.MaterializeClassified(classified, *outDir)
}
func readOperConfig(configFile string) (*configv1beta1.OperatorConfig, error) {
	operConfig := &configv1beta1.OperatorConfig{}
	_, err := os.Stat(configFile)
	if err != nil {
		return nil, err
	}

	content, err := os.ReadFile(configFile)
	if err != nil {
		return nil, err
	}

	codecs := serializer.NewCodecFactory(scheme)
	if err := runtime.DecodeInto(codecs.UniversalDecoder(), content, operConfig); err != nil {
		return nil, fmt.Errorf("could not decode file into runtime.Object: %v", err)
	}

	return operConfig, nil
}
