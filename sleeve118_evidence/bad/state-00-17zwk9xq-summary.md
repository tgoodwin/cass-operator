# Converged State Summary:
Divergence point: 
state keys:
	{PersistentVolume//pv-3d37425a:0ceea0ff-3027-4f2c-a57d-950a86feb7c7}
	{PersistentVolume//pv-6c054348:1d2a2998-e5e3-4ee5-a364-2ef4dd43fcea}
	{Endpoints/tracey/sleevecdc-seed-service:249246f4-b0eb-46a7-a55e-3d4cd34c76bd}
	{CassandraDatacenter/tracey/sample-dc:264b14f9-6b37-470f-8777-518ac6b3c6b9}
	{PersistentVolume//pv-29f7a3ad:331ca12c-f79a-44fb-b4ba-641bf6ea3b4c}
	{Endpoints/tracey/sleevecdc-sample-dc-service:4ec409a7-a13d-41ee-a367-a85886f20d32}
	{StatefulSet/tracey/sleevecdc-sample-dc-sample-rack-sts:5f73135d-1f56-45dc-a8b5-838bd26a2e46}
	{Service/tracey/sleevecdc-sample-dc-all-pods-service:782a007b-3621-4f06-8042-8902b75b9490}
	{Endpoints/tracey/sleevecdc-sample-dc-all-pods-service:782a007b-3621-4f06-8042-8902b75b9490}
	{Endpoints/tracey/sleevecdc-sample-dc-all-pods-service:7ac2e343-aeb5-4fea-8d40-797c5e13bf8d}
	{PersistentVolume//pv-7a79fb44:8b36ccb8-6cc9-448a-9774-afdb4919a157}
	{Endpoints/tracey/sleevecdc-seed-service:940d5b1c-4bc8-4688-87d2-1b57b18bc512}
	{Service/tracey/sleevecdc-seed-service:940d5b1c-4bc8-4688-87d2-1b57b18bc512}
	{PersistentVolume//pv-5d404ef3:ae1e0946-4b4a-45cf-8d42-25463f6ae9f9}
	{PersistentVolume//pv-3744934c:c431ef61-eca1-49d6-9c15-1b46ddcd2d7d}
	{Endpoints/tracey/sleevecdc-sample-dc-service:e02ba834-66ad-4ad8-8107-7a79d1b79db8}
	{Service/tracey/sleevecdc-sample-dc-service:e02ba834-66ad-4ad8-8107-7a79d1b79db8}
	{Service/tracey/sleevecdc-sample-dc-additional-seed-service:ed41f392-4004-4c3c-900b-ccf4bcaf5c8b}

## Converged Objects:
Key: {CassandraDatacenter/tracey/sample-dc:264b14f9-6b37-470f-8777-518ac6b3c6b9}
```
{
  "apiVersion": "cassandra.datastax.com/v1beta1",
  "kind": "CassandraDatacenter",
  "metadata": {
    "annotations": {
      "kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"cassandra.datastax.com/v1beta1\",\"kind\":\"CassandraDatacenter\",\"metadata\":{\"annotations\":{},\"name\":\"sample-dc\",\"namespace\":\"tracey\"},\"spec\":{\"allowMultipleNodesPerWorker\":true,\"clusterName\":\"sleevecdc\",\"config\":{\"cassandra-yaml\":{},\"jvm-server-options\":{\"initial_heap_size\":\"800M\",\"max_heap_size\":\"800M\"}},\"managementApiAuth\":{\"insecure\":{}},\"racks\":[{\"name\":\"sample-rack\"}],\"serverType\":\"cassandra\",\"serverVersion\":\"4.1.5\",\"size\":3,\"storageConfig\":{\"cassandraDataVolumeClaimSpec\":{\"accessModes\":[\"ReadWriteOnce\"],\"resources\":{\"requests\":{\"storage\":\"1Gi\"}},\"storageClassName\":\"standard\"}}}}\n"
    },
    "creationTimestamp": "2025-03-28T04:10:21Z",
    "deletionGracePeriodSeconds": 0,
    "deletionTimestamp": "2025-03-28T04:10:28Z",
    "generation": 3,
    "labels": {
      "discrete.events/change-id": "CHANGE_ID",
      "discrete.events/creator-id": "CREATOR_ID",
      "discrete.events/prev-write-reconcile-id": "RECONCILE_ID",
      "discrete.events/root-event-id": "abff6c17-4296-42f2-b594-e140dd03f7fe",
      "discrete.events/sleeve-object-id": "OBJECT_ID",
      "tracey-uid": "abff6c17-4296-42f2-b594-e140dd03f7fe"
    },
    "managedFields": [
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:kubectl.kubernetes.io/last-applied-configuration": {}
            }
          },
          "f:spec": {
            ".": {},
            "f:allowMultipleNodesPerWorker": {},
            "f:clusterName": {},
            "f:config": {
              ".": {},
              "f:cassandra-yaml": {},
              "f:jvm-server-options": {
                ".": {},
                "f:initial_heap_size": {},
                "f:max_heap_size": {}
              }
            },
            "f:managementApiAuth": {
              ".": {},
              "f:insecure": {}
            },
            "f:racks": {},
            "f:serverType": {},
            "f:serverVersion": {},
            "f:size": {},
            "f:storageConfig": {
              ".": {},
              "f:cassandraDataVolumeClaimSpec": {
                ".": {},
                "f:accessModes": {},
                "f:resources": {
                  ".": {},
                  "f:requests": {
                    ".": {},
                    "f:storage": {}
                  }
                },
                "f:storageClassName": {}
              }
            }
          }
        },
        "manager": "kubectl-client-side-apply",
        "operation": "Update",
        "time": "2025-03-28T04:10:21Z"
      },
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:finalizers": {
              ".": {},
              "v:\"finalizer.cassandra.datastax.com\"": {}
            },
            "f:labels": {
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {}
            }
          },
          "f:spec": {
            "f:additionalServiceConfig": {
              ".": {},
              "f:additionalSeedService": {},
              "f:allpodsService": {},
              "f:dcService": {},
              "f:nodePortService": {},
              "f:seedService": {}
            },
            "f:configBuilderResources": {},
            "f:resources": {},
            "f:systemLoggerResources": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:21Z"
      },
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              "f:discrete.events/change-id": {}
            }
          },
          "f:status": {
            ".": {},
            "f:cassandraOperatorProgress": {},
            "f:nodeStatuses": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:21Z"
      }
    ],
    "name": "sample-dc",
    "namespace": "tracey",
    "resourceVersion": "11176363",
    "uid": "ab21bd7e-bbd8-42b8-970d-46174c9eb384"
  },
  "spec": {
    "additionalServiceConfig": {
      "additionalSeedService": {},
      "allpodsService": {},
      "dcService": {},
      "nodePortService": {},
      "seedService": {}
    },
    "allowMultipleNodesPerWorker": true,
    "clusterName": "sleevecdc",
    "config": {
      "cassandra-yaml": {},
      "jvm-server-options": {
        "initial_heap_size": "800M",
        "max_heap_size": "800M"
      }
    },
    "configBuilderResources": {},
    "managementApiAuth": {
      "insecure": {}
    },
    "racks": [
      {
        "name": "sample-rack"
      }
    ],
    "resources": {},
    "serverType": "cassandra",
    "serverVersion": "4.1.5",
    "size": 3,
    "storageConfig": {
      "cassandraDataVolumeClaimSpec": {
        "accessModes": [
          "ReadWriteOnce"
        ],
        "resources": {
          "requests": {
            "storage": "1Gi"
          }
        },
        "storageClassName": "standard"
      }
    },
    "systemLoggerResources": {}
  },
  "status": {
    "cassandraOperatorProgress": "Updating",
    "lastRollingRestart": "1970-01-01T00:00:01Z",
    "lastServerNodeStarted": "1970-01-01T00:00:01Z",
    "nodeReplacements": null,
    "nodeStatuses": {},
    "quietPeriod": null,
    "superUserUpserted": "1970-01-01T00:00:01Z",
    "usersUpserted": null
  }
}
```
Key: {Endpoints/tracey/sleevecdc-seed-service:249246f4-b0eb-46a7-a55e-3d4cd34c76bd}
```
{
  "apiVersion": "v1",
  "kind": "Endpoints",
  "metadata": {
    "annotations": {
      "endpoints.kubernetes.io/last-change-trigger-time": "2025-03-28T04:10:21Z"
    },
    "creationTimestamp": "2025-03-28T04:10:21Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "discrete.events/change-id": "c10034b1-91ce-4203-bac1-005a7375fa6c",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "3c57805e-bb90-495d-a8ef-f29da58a0f5e",
      "discrete.events/root-event-id": "abff6c17-4296-42f2-b594-e140dd03f7fe",
      "discrete.events/sleeve-object-id": "249246f4-b0eb-46a7-a55e-3d4cd34c76bd",
      "service.kubernetes.io/headless": ""
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:endpoints.kubernetes.io/last-change-trigger-time": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {},
              "f:service.kubernetes.io/headless": {}
            }
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "time": "2025-03-28T04:10:21Z"
      }
    ],
    "name": "sleevecdc-seed-service",
    "namespace": "tracey",
    "resourceVersion": "11176301",
    "uid": "8e1b3b36-a5b4-415f-b6cb-c9de8ded6820"
  }
}
```
Key: {Endpoints/tracey/sleevecdc-sample-dc-service:4ec409a7-a13d-41ee-a367-a85886f20d32}
```
{
  "apiVersion": "v1",
  "kind": "Endpoints",
  "metadata": {
    "annotations": {
      "endpoints.kubernetes.io/last-change-trigger-time": "2025-03-28T04:10:21Z"
    },
    "creationTimestamp": "2025-03-28T04:10:21Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "discrete.events/change-id": "25ea7a09-588d-4ea6-bd9a-612dacdfc0c0",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "3c57805e-bb90-495d-a8ef-f29da58a0f5e",
      "discrete.events/root-event-id": "abff6c17-4296-42f2-b594-e140dd03f7fe",
      "discrete.events/sleeve-object-id": "4ec409a7-a13d-41ee-a367-a85886f20d32",
      "service.kubernetes.io/headless": ""
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:endpoints.kubernetes.io/last-change-trigger-time": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {},
              "f:service.kubernetes.io/headless": {}
            }
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "time": "2025-03-28T04:10:21Z"
      }
    ],
    "name": "sleevecdc-sample-dc-service",
    "namespace": "tracey",
    "resourceVersion": "11176299",
    "uid": "cad3da86-dca7-4479-a48b-670aaff9123e"
  }
}
```
Key: {Endpoints/tracey/sleevecdc-sample-dc-all-pods-service:782a007b-3621-4f06-8042-8902b75b9490}
```
{
  "apiVersion": "v1",
  "kind": "Endpoints",
  "metadata": {
    "annotations": {
      "endpoints.kubernetes.io/last-change-trigger-time": "2025-03-28T04:10:31Z"
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "cassandra.datastax.com/prom-metrics": "true",
      "discrete.events/change-id": "05766ec1-3846-4986-9325-92876fa564d6",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "782a007b-3621-4f06-8042-8902b75b9490",
      "service.kubernetes.io/headless": ""
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:endpoints.kubernetes.io/last-change-trigger-time": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:cassandra.datastax.com/prom-metrics": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {},
              "f:service.kubernetes.io/headless": {}
            }
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-sample-dc-all-pods-service",
    "namespace": "tracey",
    "resourceVersion": "11176423",
    "uid": "0e3cb940-3710-493f-8b42-c60fcd8cec04"
  }
}
```
Key: {Endpoints/tracey/sleevecdc-sample-dc-all-pods-service:7ac2e343-aeb5-4fea-8d40-797c5e13bf8d}
```
{
  "apiVersion": "v1",
  "kind": "Endpoints",
  "metadata": {
    "annotations": {
      "endpoints.kubernetes.io/last-change-trigger-time": "2025-03-28T04:10:21Z"
    },
    "creationTimestamp": "2025-03-28T04:10:21Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "cassandra.datastax.com/prom-metrics": "true",
      "discrete.events/change-id": "fb3159eb-b309-4891-bfce-4e2e99378543",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "3c57805e-bb90-495d-a8ef-f29da58a0f5e",
      "discrete.events/root-event-id": "abff6c17-4296-42f2-b594-e140dd03f7fe",
      "discrete.events/sleeve-object-id": "7ac2e343-aeb5-4fea-8d40-797c5e13bf8d",
      "service.kubernetes.io/headless": ""
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:endpoints.kubernetes.io/last-change-trigger-time": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:cassandra.datastax.com/prom-metrics": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {},
              "f:service.kubernetes.io/headless": {}
            }
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "time": "2025-03-28T04:10:21Z"
      }
    ],
    "name": "sleevecdc-sample-dc-all-pods-service",
    "namespace": "tracey",
    "resourceVersion": "11176304",
    "uid": "2156195d-f618-4998-aa58-c3d19b0015d9"
  }
}
```
Key: {Endpoints/tracey/sleevecdc-seed-service:940d5b1c-4bc8-4688-87d2-1b57b18bc512}
```
{
  "apiVersion": "v1",
  "kind": "Endpoints",
  "metadata": {
    "annotations": {
      "endpoints.kubernetes.io/last-change-trigger-time": "2025-03-28T04:10:31Z"
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "discrete.events/change-id": "807e2dcc-90b4-4709-ac72-0e9845ceb882",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "940d5b1c-4bc8-4688-87d2-1b57b18bc512",
      "service.kubernetes.io/headless": ""
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:endpoints.kubernetes.io/last-change-trigger-time": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {},
              "f:service.kubernetes.io/headless": {}
            }
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-seed-service",
    "namespace": "tracey",
    "resourceVersion": "11176420",
    "uid": "637281a7-8f0a-4e34-ab33-01b27851d03d"
  }
}
```
Key: {Endpoints/tracey/sleevecdc-sample-dc-service:e02ba834-66ad-4ad8-8107-7a79d1b79db8}
```
{
  "apiVersion": "v1",
  "kind": "Endpoints",
  "metadata": {
    "annotations": {
      "endpoints.kubernetes.io/last-change-trigger-time": "2025-03-28T04:10:31Z"
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "discrete.events/change-id": "ef22d39c-c48d-4b8e-9d15-560f09fe8c8e",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "e02ba834-66ad-4ad8-8107-7a79d1b79db8",
      "service.kubernetes.io/headless": ""
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:endpoints.kubernetes.io/last-change-trigger-time": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {},
              "f:service.kubernetes.io/headless": {}
            }
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-sample-dc-service",
    "namespace": "tracey",
    "resourceVersion": "11176417",
    "uid": "3173a841-25e6-4a3a-874a-efe664a98ffb"
  }
}
```
Key: {PersistentVolume//pv-3d37425a:0ceea0ff-3027-4f2c-a57d-950a86feb7c7}
```
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "metadata": {
    "annotations": {
      "pv.kubernetes.io/bound-by-controller": "yes"
    },
    "creationTimestamp": "2025-03-28T04:10:40Z",
    "finalizers": [
      "kubernetes.io/pv-protection"
    ],
    "labels": {
      "discrete.events/change-id": "03aed3aa-a63d-44f9-8072-b46f384e1e67",
      "discrete.events/creator-id": "PersistentVolumeClaimReconciler",
      "discrete.events/prev-write-reconcile-id": "607b691b-d7bc-4c12-ab36-624a2c7be676",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "0ceea0ff-3027-4f2c-a57d-950a86feb7c7"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              ".": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            }
          },
          "f:spec": {
            "f:accessModes": {},
            "f:capacity": {
              ".": {},
              "f:storage": {}
            },
            "f:hostPath": {
              ".": {},
              "f:path": {},
              "f:type": {}
            },
            "f:persistentVolumeReclaimPolicy": {},
            "f:storageClassName": {},
            "f:volumeMode": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:40Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:phase": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:42Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:pv.kubernetes.io/bound-by-controller": {}
            }
          },
          "f:spec": {
            "f:claimRef": {
              ".": {},
              "f:apiVersion": {},
              "f:kind": {},
              "f:name": {},
              "f:namespace": {},
              "f:resourceVersion": {},
              "f:uid": {}
            }
          }
        },
        "manager": "kube-scheduler",
        "operation": "Update",
        "time": "2025-03-28T04:10:42Z"
      }
    ],
    "name": "pv-3d37425a",
    "resourceVersion": "11176492",
    "uid": "f545f561-43cc-42c1-9b2e-7088bca44e54"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "capacity": {
      "storage": "1Gi"
    },
    "claimRef": {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "name": "server-data-sleevecdc-sample-dc-sample-rack-sts-2",
      "namespace": "tracey",
      "resourceVersion": "11176445",
      "uid": "c04d4867-3d4e-4e19-92d2-5597d98ad738"
    },
    "hostPath": {
      "path": "/tmp/sleeve-pv/pv-3d37425a",
      "type": ""
    },
    "persistentVolumeReclaimPolicy": "Retain",
    "storageClassName": "standard",
    "volumeMode": "Filesystem"
  },
  "status": {
    "phase": "Bound"
  }
}
```
Key: {PersistentVolume//pv-6c054348:1d2a2998-e5e3-4ee5-a364-2ef4dd43fcea}
```
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "metadata": {
    "creationTimestamp": "2025-03-28T01:03:19Z",
    "finalizers": [
      "kubernetes.io/pv-protection"
    ],
    "labels": {
      "discrete.events/change-id": "7b1e3653-6150-44a3-a452-32085d1f8561",
      "discrete.events/creator-id": "PersistentVolumeClaimReconciler",
      "discrete.events/prev-write-reconcile-id": "961be085-d132-4271-a01b-619f470afd09",
      "discrete.events/root-event-id": "d6f156dc-316c-40ce-b7d7-96b85e9b74f3",
      "discrete.events/sleeve-object-id": "1d2a2998-e5e3-4ee5-a364-2ef4dd43fcea"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              ".": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            }
          },
          "f:spec": {
            "f:accessModes": {},
            "f:capacity": {
              ".": {},
              "f:storage": {}
            },
            "f:claimRef": {
              ".": {},
              "f:apiVersion": {},
              "f:kind": {},
              "f:name": {},
              "f:namespace": {},
              "f:uid": {}
            },
            "f:hostPath": {
              ".": {},
              "f:path": {},
              "f:type": {}
            },
            "f:persistentVolumeReclaimPolicy": {},
            "f:storageClassName": {},
            "f:volumeMode": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:27Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:phase": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:28Z"
      }
    ],
    "name": "pv-6c054348",
    "resourceVersion": "11176390",
    "uid": "26232b37-d6f1-4e45-abc7-73bcbddb9877"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "capacity": {
      "storage": "1Gi"
    },
    "claimRef": {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "name": "server-data-sleevecdc-sample-dc-sample-rack-sts-2",
      "namespace": "tracey",
      "uid": "038daa39-8147-4416-af7c-274d030839e9"
    },
    "hostPath": {
      "path": "/tmp/sleeve-pv/pv-6c054348",
      "type": ""
    },
    "persistentVolumeReclaimPolicy": "Retain",
    "storageClassName": "standard",
    "volumeMode": "Filesystem"
  },
  "status": {
    "phase": "Released"
  }
}
```
Key: {PersistentVolume//pv-29f7a3ad:331ca12c-f79a-44fb-b4ba-641bf6ea3b4c}
```
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "metadata": {
    "creationTimestamp": "2025-03-28T04:10:37Z",
    "finalizers": [
      "kubernetes.io/pv-protection"
    ],
    "labels": {
      "discrete.events/change-id": "e681a970-41bb-4c63-b2f1-cba53859eb2f",
      "discrete.events/creator-id": "PersistentVolumeClaimReconciler",
      "discrete.events/prev-write-reconcile-id": "d375f318-10af-4bd3-85fe-a2d0d9795565",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "331ca12c-f79a-44fb-b4ba-641bf6ea3b4c"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:phase": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:39Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              ".": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            }
          },
          "f:spec": {
            "f:accessModes": {},
            "f:capacity": {
              ".": {},
              "f:storage": {}
            },
            "f:claimRef": {
              ".": {},
              "f:apiVersion": {},
              "f:kind": {},
              "f:name": {},
              "f:namespace": {},
              "f:uid": {}
            },
            "f:hostPath": {
              ".": {},
              "f:path": {},
              "f:type": {}
            },
            "f:persistentVolumeReclaimPolicy": {},
            "f:storageClassName": {},
            "f:volumeMode": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:39Z"
      }
    ],
    "name": "pv-29f7a3ad",
    "resourceVersion": "11176481",
    "uid": "1f563f9b-52db-440b-bf2b-177e1d3452bb"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "capacity": {
      "storage": "1Gi"
    },
    "claimRef": {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "name": "server-data-sleevecdc-sample-dc-sample-rack-sts-0",
      "namespace": "tracey",
      "uid": "549c8149-ba30-4a3f-ab23-b50b6179b0d6"
    },
    "hostPath": {
      "path": "/tmp/sleeve-pv/pv-29f7a3ad",
      "type": ""
    },
    "persistentVolumeReclaimPolicy": "Retain",
    "storageClassName": "standard",
    "volumeMode": "Filesystem"
  },
  "status": {
    "phase": "Bound"
  }
}
```
Key: {PersistentVolume//pv-7a79fb44:8b36ccb8-6cc9-448a-9774-afdb4919a157}
```
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "metadata": {
    "creationTimestamp": "2025-03-28T01:03:03Z",
    "finalizers": [
      "kubernetes.io/pv-protection"
    ],
    "labels": {
      "discrete.events/change-id": "dcfdcf17-f7b1-42c5-9d61-14ba9980b5e1",
      "discrete.events/creator-id": "PersistentVolumeClaimReconciler",
      "discrete.events/prev-write-reconcile-id": "5aa2a1dc-a89b-475c-9674-95110c5ecb56",
      "discrete.events/root-event-id": "6cb96057-029b-4029-94e8-eef90a2dc8c6",
      "discrete.events/sleeve-object-id": "8b36ccb8-6cc9-448a-9774-afdb4919a157"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              ".": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            }
          },
          "f:spec": {
            "f:accessModes": {},
            "f:capacity": {
              ".": {},
              "f:storage": {}
            },
            "f:claimRef": {
              ".": {},
              "f:apiVersion": {},
              "f:kind": {},
              "f:name": {},
              "f:namespace": {},
              "f:uid": {}
            },
            "f:hostPath": {
              ".": {},
              "f:path": {},
              "f:type": {}
            },
            "f:persistentVolumeReclaimPolicy": {},
            "f:storageClassName": {},
            "f:volumeMode": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:25Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:phase": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:28Z"
      }
    ],
    "name": "pv-7a79fb44",
    "resourceVersion": "11176392",
    "uid": "2a3af99e-4783-4817-9c84-d12d6798396d"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "capacity": {
      "storage": "1Gi"
    },
    "claimRef": {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "name": "server-data-sleevecdc-sample-dc-sample-rack-sts-1",
      "namespace": "tracey",
      "uid": "964cd76e-164c-4a7b-8ea3-73da2700c618"
    },
    "hostPath": {
      "path": "/tmp/sleeve-pv/pv-7a79fb44",
      "type": ""
    },
    "persistentVolumeReclaimPolicy": "Retain",
    "storageClassName": "standard",
    "volumeMode": "Filesystem"
  },
  "status": {
    "phase": "Released"
  }
}
```
Key: {PersistentVolume//pv-5d404ef3:ae1e0946-4b4a-45cf-8d42-25463f6ae9f9}
```
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "metadata": {
    "annotations": {
      "pv.kubernetes.io/bound-by-controller": "yes"
    },
    "creationTimestamp": "2025-03-28T04:10:33Z",
    "finalizers": [
      "kubernetes.io/pv-protection"
    ],
    "labels": {
      "discrete.events/change-id": "c09b2ffc-ef9b-42a0-ac38-062b23805928",
      "discrete.events/creator-id": "PersistentVolumeClaimReconciler",
      "discrete.events/prev-write-reconcile-id": "de0daea8-8e42-4390-a33e-127fb5a5590d",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "ae1e0946-4b4a-45cf-8d42-25463f6ae9f9"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              ".": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            }
          },
          "f:spec": {
            "f:accessModes": {},
            "f:capacity": {
              ".": {},
              "f:storage": {}
            },
            "f:hostPath": {
              ".": {},
              "f:path": {},
              "f:type": {}
            },
            "f:persistentVolumeReclaimPolicy": {},
            "f:storageClassName": {},
            "f:volumeMode": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:33Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:phase": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:34Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:pv.kubernetes.io/bound-by-controller": {}
            }
          },
          "f:spec": {
            "f:claimRef": {
              ".": {},
              "f:apiVersion": {},
              "f:kind": {},
              "f:name": {},
              "f:namespace": {},
              "f:resourceVersion": {},
              "f:uid": {}
            }
          }
        },
        "manager": "kube-scheduler",
        "operation": "Update",
        "time": "2025-03-28T04:10:34Z"
      }
    ],
    "name": "pv-5d404ef3",
    "resourceVersion": "11176466",
    "uid": "328e51ea-6be3-401f-a4fa-bf14fc73d37b"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "capacity": {
      "storage": "1Gi"
    },
    "claimRef": {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "name": "server-data-sleevecdc-sample-dc-sample-rack-sts-1",
      "namespace": "tracey",
      "resourceVersion": "11176439",
      "uid": "38e9b5b5-8c41-4b1c-ba89-5591335321a0"
    },
    "hostPath": {
      "path": "/tmp/sleeve-pv/pv-5d404ef3",
      "type": ""
    },
    "persistentVolumeReclaimPolicy": "Retain",
    "storageClassName": "standard",
    "volumeMode": "Filesystem"
  },
  "status": {
    "phase": "Bound"
  }
}
```
Key: {PersistentVolume//pv-3744934c:c431ef61-eca1-49d6-9c15-1b46ddcd2d7d}
```
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "metadata": {
    "creationTimestamp": "2025-03-28T01:03:02Z",
    "finalizers": [
      "kubernetes.io/pv-protection"
    ],
    "labels": {
      "discrete.events/change-id": "0d59a5fc-7c3b-426d-b4b0-f5373e18e89a",
      "discrete.events/creator-id": "PersistentVolumeClaimReconciler",
      "discrete.events/prev-write-reconcile-id": "f6da316b-c9b0-48fa-b255-e87af0d68710",
      "discrete.events/root-event-id": "6cb96057-029b-4029-94e8-eef90a2dc8c6",
      "discrete.events/sleeve-object-id": "c431ef61-eca1-49d6-9c15-1b46ddcd2d7d"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:labels": {
              ".": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            }
          },
          "f:spec": {
            "f:accessModes": {},
            "f:capacity": {
              ".": {},
              "f:storage": {}
            },
            "f:claimRef": {
              ".": {},
              "f:apiVersion": {},
              "f:kind": {},
              "f:name": {},
              "f:namespace": {},
              "f:uid": {}
            },
            "f:hostPath": {
              ".": {},
              "f:path": {},
              "f:type": {}
            },
            "f:persistentVolumeReclaimPolicy": {},
            "f:storageClassName": {},
            "f:volumeMode": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:23Z"
      },
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:phase": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:28Z"
      }
    ],
    "name": "pv-3744934c",
    "resourceVersion": "11176383",
    "uid": "3fc0bc19-2bec-42ae-8962-214b7b954a68"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "capacity": {
      "storage": "1Gi"
    },
    "claimRef": {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "name": "server-data-sleevecdc-sample-dc-sample-rack-sts-0",
      "namespace": "tracey",
      "uid": "80dac9ef-01ab-4232-b38b-aa9be3fa8e7f"
    },
    "hostPath": {
      "path": "/tmp/sleeve-pv/pv-3744934c",
      "type": ""
    },
    "persistentVolumeReclaimPolicy": "Retain",
    "storageClassName": "standard",
    "volumeMode": "Filesystem"
  },
  "status": {
    "phase": "Released"
  }
}
```
Key: {Service/tracey/sleevecdc-sample-dc-all-pods-service:782a007b-3621-4f06-8042-8902b75b9490}
```
{
  "apiVersion": "v1",
  "kind": "Service",
  "metadata": {
    "annotations": {
      "cassandra.datastax.com/resource-hash": "tgTsQ5lo0spL0L3cuVADRzaFsTVkQLs93t7Xd0NwAso="
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "cassandra.datastax.com/prom-metrics": "true",
      "discrete.events/change-id": "05766ec1-3846-4986-9325-92876fa564d6",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "782a007b-3621-4f06-8042-8902b75b9490"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:cassandra.datastax.com/resource-hash": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:cassandra.datastax.com/prom-metrics": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            },
            "f:ownerReferences": {
              ".": {},
              "k:{\"uid\":\"f41bd5db-5b03-483a-8eb6-ab7aba48b540\"}": {}
            }
          },
          "f:spec": {
            "f:clusterIP": {},
            "f:internalTrafficPolicy": {},
            "f:ports": {
              ".": {},
              "k:{\"port\":8080,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9000,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9042,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9103,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              }
            },
            "f:publishNotReadyAddresses": {},
            "f:selector": {},
            "f:sessionAffinity": {},
            "f:type": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-sample-dc-all-pods-service",
    "namespace": "tracey",
    "ownerReferences": [
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "blockOwnerDeletion": true,
        "controller": true,
        "kind": "CassandraDatacenter",
        "name": "sample-dc",
        "uid": "f41bd5db-5b03-483a-8eb6-ab7aba48b540"
      }
    ],
    "resourceVersion": "11176422",
    "uid": "f9ad5a75-c66d-48c2-a0b1-fe17481307e6"
  },
  "spec": {
    "clusterIP": "None",
    "clusterIPs": [
      "None"
    ],
    "internalTrafficPolicy": "Cluster",
    "ipFamilies": [
      "IPv4"
    ],
    "ipFamilyPolicy": "SingleStack",
    "ports": [
      {
        "name": "native",
        "port": 9042,
        "protocol": "TCP",
        "targetPort": 9042
      },
      {
        "name": "mgmt-api",
        "port": 8080,
        "protocol": "TCP",
        "targetPort": 8080
      },
      {
        "name": "prometheus",
        "port": 9103,
        "protocol": "TCP",
        "targetPort": 9103
      },
      {
        "name": "metrics",
        "port": 9000,
        "protocol": "TCP",
        "targetPort": 9000
      }
    ],
    "publishNotReadyAddresses": true,
    "selector": {
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc"
    },
    "sessionAffinity": "None",
    "type": "ClusterIP"
  },
  "status": {
    "loadBalancer": {}
  }
}
```
Key: {Service/tracey/sleevecdc-seed-service:940d5b1c-4bc8-4688-87d2-1b57b18bc512}
```
{
  "apiVersion": "v1",
  "kind": "Service",
  "metadata": {
    "annotations": {
      "cassandra.datastax.com/resource-hash": "D+i3/0rp29bPP2bMACiSvkC5xlKJr0QsyUkRt8fNvPY=",
      "kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"cassandra.datastax.com/v1beta1\",\"kind\":\"CassandraDatacenter\",\"metadata\":{\"annotations\":{},\"name\":\"sample-dc\",\"namespace\":\"tracey\"},\"spec\":{\"allowMultipleNodesPerWorker\":true,\"clusterName\":\"sleevecdc\",\"config\":{\"cassandra-yaml\":{},\"jvm-server-options\":{\"initial_heap_size\":\"800M\",\"max_heap_size\":\"800M\"}},\"managementApiAuth\":{\"insecure\":{}},\"racks\":[{\"name\":\"sample-rack\"}],\"serverType\":\"cassandra\",\"serverVersion\":\"4.1.5\",\"size\":3,\"storageConfig\":{\"cassandraDataVolumeClaimSpec\":{\"accessModes\":[\"ReadWriteOnce\"],\"resources\":{\"requests\":{\"storage\":\"1Gi\"}},\"storageClassName\":\"standard\"}}}}\n"
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "discrete.events/change-id": "807e2dcc-90b4-4709-ac72-0e9845ceb882",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "940d5b1c-4bc8-4688-87d2-1b57b18bc512"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:cassandra.datastax.com/resource-hash": {},
              "f:kubectl.kubernetes.io/last-applied-configuration": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            },
            "f:ownerReferences": {
              ".": {},
              "k:{\"uid\":\"f41bd5db-5b03-483a-8eb6-ab7aba48b540\"}": {}
            }
          },
          "f:spec": {
            "f:clusterIP": {},
            "f:internalTrafficPolicy": {},
            "f:publishNotReadyAddresses": {},
            "f:selector": {},
            "f:sessionAffinity": {},
            "f:type": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-seed-service",
    "namespace": "tracey",
    "ownerReferences": [
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "blockOwnerDeletion": true,
        "controller": true,
        "kind": "CassandraDatacenter",
        "name": "sample-dc",
        "uid": "f41bd5db-5b03-483a-8eb6-ab7aba48b540"
      }
    ],
    "resourceVersion": "11176419",
    "uid": "3ac3950c-7e9d-47fc-bec0-92d0a0fedaa9"
  },
  "spec": {
    "clusterIP": "None",
    "clusterIPs": [
      "None"
    ],
    "internalTrafficPolicy": "Cluster",
    "ipFamilies": [
      "IPv4"
    ],
    "ipFamilyPolicy": "SingleStack",
    "publishNotReadyAddresses": true,
    "selector": {
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/seed-node": "true"
    },
    "sessionAffinity": "None",
    "type": "ClusterIP"
  },
  "status": {
    "loadBalancer": {}
  }
}
```
Key: {Service/tracey/sleevecdc-sample-dc-service:e02ba834-66ad-4ad8-8107-7a79d1b79db8}
```
{
  "apiVersion": "v1",
  "kind": "Service",
  "metadata": {
    "annotations": {
      "cassandra.datastax.com/resource-hash": "ExdytUM/fR9qZGfbBrU6EgaCzUE7KWMSF8rVBoO8EFs="
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "discrete.events/change-id": "ef22d39c-c48d-4b8e-9d15-560f09fe8c8e",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "e02ba834-66ad-4ad8-8107-7a79d1b79db8"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:cassandra.datastax.com/resource-hash": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            },
            "f:ownerReferences": {
              ".": {},
              "k:{\"uid\":\"f41bd5db-5b03-483a-8eb6-ab7aba48b540\"}": {}
            }
          },
          "f:spec": {
            "f:clusterIP": {},
            "f:internalTrafficPolicy": {},
            "f:ports": {
              ".": {},
              "k:{\"port\":8080,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9000,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9042,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9103,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              },
              "k:{\"port\":9142,\"protocol\":\"TCP\"}": {
                ".": {},
                "f:name": {},
                "f:port": {},
                "f:protocol": {},
                "f:targetPort": {}
              }
            },
            "f:selector": {},
            "f:sessionAffinity": {},
            "f:type": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-sample-dc-service",
    "namespace": "tracey",
    "ownerReferences": [
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "blockOwnerDeletion": true,
        "controller": true,
        "kind": "CassandraDatacenter",
        "name": "sample-dc",
        "uid": "f41bd5db-5b03-483a-8eb6-ab7aba48b540"
      }
    ],
    "resourceVersion": "11176416",
    "uid": "73702f47-62c3-4190-a27f-a99cbec8389b"
  },
  "spec": {
    "clusterIP": "None",
    "clusterIPs": [
      "None"
    ],
    "internalTrafficPolicy": "Cluster",
    "ipFamilies": [
      "IPv4"
    ],
    "ipFamilyPolicy": "SingleStack",
    "ports": [
      {
        "name": "native",
        "port": 9042,
        "protocol": "TCP",
        "targetPort": 9042
      },
      {
        "name": "tls-native",
        "port": 9142,
        "protocol": "TCP",
        "targetPort": 9142
      },
      {
        "name": "mgmt-api",
        "port": 8080,
        "protocol": "TCP",
        "targetPort": 8080
      },
      {
        "name": "prometheus",
        "port": 9103,
        "protocol": "TCP",
        "targetPort": 9103
      },
      {
        "name": "metrics",
        "port": 9000,
        "protocol": "TCP",
        "targetPort": 9000
      }
    ],
    "selector": {
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc"
    },
    "sessionAffinity": "None",
    "type": "ClusterIP"
  },
  "status": {
    "loadBalancer": {}
  }
}
```
Key: {Service/tracey/sleevecdc-sample-dc-additional-seed-service:ed41f392-4004-4c3c-900b-ccf4bcaf5c8b}
```
{
  "apiVersion": "v1",
  "kind": "Service",
  "metadata": {
    "annotations": {
      "cassandra.datastax.com/resource-hash": "qBiInEaUBeCyhOUmCnYpKBj4MlcmR0pYUBFVvVtJ2H0="
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "discrete.events/change-id": "80c5e6b7-1b1f-4b60-ab3f-41ed70f47af1",
      "discrete.events/creator-id": "CassandraDatacenter",
      "discrete.events/prev-write-reconcile-id": "6cb487ee-71f4-4f3e-bc9f-f5168d5d1d92",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "ed41f392-4004-4c3c-900b-ccf4bcaf5c8b"
    },
    "managedFields": [
      {
        "apiVersion": "v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:cassandra.datastax.com/resource-hash": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            },
            "f:ownerReferences": {
              ".": {},
              "k:{\"uid\":\"f41bd5db-5b03-483a-8eb6-ab7aba48b540\"}": {}
            }
          },
          "f:spec": {
            "f:clusterIP": {},
            "f:internalTrafficPolicy": {},
            "f:publishNotReadyAddresses": {},
            "f:sessionAffinity": {},
            "f:type": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      }
    ],
    "name": "sleevecdc-sample-dc-additional-seed-service",
    "namespace": "tracey",
    "ownerReferences": [
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "blockOwnerDeletion": true,
        "controller": true,
        "kind": "CassandraDatacenter",
        "name": "sample-dc",
        "uid": "f41bd5db-5b03-483a-8eb6-ab7aba48b540"
      }
    ],
    "resourceVersion": "11176425",
    "uid": "80ee9231-a175-4e2f-9f92-0fe76eb4ceba"
  },
  "spec": {
    "clusterIP": "None",
    "clusterIPs": [
      "None"
    ],
    "internalTrafficPolicy": "Cluster",
    "ipFamilies": [
      "IPv4",
      "IPv6"
    ],
    "ipFamilyPolicy": "RequireDualStack",
    "publishNotReadyAddresses": true,
    "sessionAffinity": "None",
    "type": "ClusterIP"
  },
  "status": {
    "loadBalancer": {}
  }
}
```
Key: {StatefulSet/tracey/sleevecdc-sample-dc-sample-rack-sts:5f73135d-1f56-45dc-a8b5-838bd26a2e46}
```
{
  "apiVersion": "apps/v1",
  "kind": "StatefulSet",
  "metadata": {
    "annotations": {
      "cassandra.datastax.com/resource-hash": "7aVuAh04+l/t8FDW/ZMZaMGcNb96V6HQViwhmQMCSs4="
    },
    "creationTimestamp": "2025-03-28T04:10:31Z",
    "generation": 1,
    "labels": {
      "app.kubernetes.io/created-by": "cass-operator",
      "app.kubernetes.io/instance": "cassandra-sleevecdc",
      "app.kubernetes.io/managed-by": "cass-operator",
      "app.kubernetes.io/name": "cassandra",
      "app.kubernetes.io/version": "4.1.5",
      "cassandra.datastax.com/cluster": "sleevecdc",
      "cassandra.datastax.com/datacenter": "sample-dc",
      "cassandra.datastax.com/rack": "sample-rack",
      "discrete.events/change-id": "CHANGE_ID",
      "discrete.events/creator-id": "CREATOR_ID",
      "discrete.events/prev-write-reconcile-id": "RECONCILE_ID",
      "discrete.events/root-event-id": "ca7ff713-a333-490c-92cf-6d19a1018e84",
      "discrete.events/sleeve-object-id": "OBJECT_ID"
    },
    "managedFields": [
      {
        "apiVersion": "apps/v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:metadata": {
            "f:annotations": {
              ".": {},
              "f:cassandra.datastax.com/resource-hash": {}
            },
            "f:labels": {
              ".": {},
              "f:app.kubernetes.io/created-by": {},
              "f:app.kubernetes.io/instance": {},
              "f:app.kubernetes.io/managed-by": {},
              "f:app.kubernetes.io/name": {},
              "f:app.kubernetes.io/version": {},
              "f:cassandra.datastax.com/cluster": {},
              "f:cassandra.datastax.com/datacenter": {},
              "f:cassandra.datastax.com/rack": {},
              "f:discrete.events/change-id": {},
              "f:discrete.events/creator-id": {},
              "f:discrete.events/prev-write-reconcile-id": {},
              "f:discrete.events/root-event-id": {},
              "f:discrete.events/sleeve-object-id": {}
            },
            "f:ownerReferences": {
              ".": {},
              "k:{\"uid\":\"f41bd5db-5b03-483a-8eb6-ab7aba48b540\"}": {}
            }
          },
          "f:spec": {
            "f:minReadySeconds": {},
            "f:podManagementPolicy": {},
            "f:replicas": {},
            "f:revisionHistoryLimit": {},
            "f:selector": {},
            "f:serviceName": {},
            "f:template": {
              "f:metadata": {
                "f:labels": {
                  ".": {},
                  "f:app.kubernetes.io/created-by": {},
                  "f:app.kubernetes.io/instance": {},
                  "f:app.kubernetes.io/managed-by": {},
                  "f:app.kubernetes.io/name": {},
                  "f:app.kubernetes.io/version": {},
                  "f:cassandra.datastax.com/cluster": {},
                  "f:cassandra.datastax.com/datacenter": {},
                  "f:cassandra.datastax.com/node-state": {},
                  "f:cassandra.datastax.com/rack": {}
                }
              },
              "f:spec": {
                "f:affinity": {},
                "f:containers": {
                  "k:{\"name\":\"cassandra\"}": {
                    ".": {},
                    "f:env": {
                      ".": {},
                      "k:{\"name\":\"DS_LICENSE\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"MGMT_API_EXPLICIT_START\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"MGMT_API_NO_KEEP_ALIVE\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"NODE_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"POD_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"USE_MGMT_API\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      }
                    },
                    "f:image": {},
                    "f:imagePullPolicy": {},
                    "f:lifecycle": {
                      ".": {},
                      "f:preStop": {
                        ".": {},
                        "f:exec": {
                          ".": {},
                          "f:command": {}
                        }
                      }
                    },
                    "f:livenessProbe": {
                      ".": {},
                      "f:failureThreshold": {},
                      "f:httpGet": {
                        ".": {},
                        "f:path": {},
                        "f:port": {},
                        "f:scheme": {}
                      },
                      "f:initialDelaySeconds": {},
                      "f:periodSeconds": {},
                      "f:successThreshold": {},
                      "f:timeoutSeconds": {}
                    },
                    "f:name": {},
                    "f:ports": {
                      ".": {},
                      "k:{\"containerPort\":7000,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":7001,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":7199,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":8080,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":9000,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":9042,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":9103,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      },
                      "k:{\"containerPort\":9142,\"protocol\":\"TCP\"}": {
                        ".": {},
                        "f:containerPort": {},
                        "f:name": {},
                        "f:protocol": {}
                      }
                    },
                    "f:readinessProbe": {
                      ".": {},
                      "f:failureThreshold": {},
                      "f:httpGet": {
                        ".": {},
                        "f:path": {},
                        "f:port": {},
                        "f:scheme": {}
                      },
                      "f:initialDelaySeconds": {},
                      "f:periodSeconds": {},
                      "f:successThreshold": {},
                      "f:timeoutSeconds": {}
                    },
                    "f:resources": {},
                    "f:terminationMessagePath": {},
                    "f:terminationMessagePolicy": {},
                    "f:volumeMounts": {
                      ".": {},
                      "k:{\"mountPath\":\"/config\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      },
                      "k:{\"mountPath\":\"/var/lib/cassandra\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      },
                      "k:{\"mountPath\":\"/var/log/cassandra\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      }
                    }
                  },
                  "k:{\"name\":\"server-system-logger\"}": {
                    ".": {},
                    "f:env": {
                      ".": {},
                      "k:{\"name\":\"CLUSTER_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"DATACENTER_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"NAMESPACE\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"NODE_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"POD_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"RACK_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      }
                    },
                    "f:image": {},
                    "f:imagePullPolicy": {},
                    "f:name": {},
                    "f:resources": {
                      ".": {},
                      "f:limits": {
                        ".": {},
                        "f:memory": {}
                      },
                      "f:requests": {
                        ".": {},
                        "f:cpu": {},
                        "f:memory": {}
                      }
                    },
                    "f:terminationMessagePath": {},
                    "f:terminationMessagePolicy": {},
                    "f:volumeMounts": {
                      ".": {},
                      "k:{\"mountPath\":\"/var/lib/vector\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      },
                      "k:{\"mountPath\":\"/var/log/cassandra\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      }
                    }
                  }
                },
                "f:dnsPolicy": {},
                "f:initContainers": {
                  ".": {},
                  "k:{\"name\":\"server-config-init\"}": {
                    ".": {},
                    "f:args": {},
                    "f:env": {
                      ".": {},
                      "k:{\"name\":\"CONFIG_FILE_DATA\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"HOST_IP\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"POD_IP\"}": {
                        ".": {},
                        "f:name": {},
                        "f:valueFrom": {
                          ".": {},
                          "f:fieldRef": {}
                        }
                      },
                      "k:{\"name\":\"PRODUCT_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"PRODUCT_VERSION\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"RACK_NAME\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      },
                      "k:{\"name\":\"USE_HOST_IP_FOR_BROADCAST\"}": {
                        ".": {},
                        "f:name": {},
                        "f:value": {}
                      }
                    },
                    "f:image": {},
                    "f:imagePullPolicy": {},
                    "f:name": {},
                    "f:resources": {
                      ".": {},
                      "f:limits": {
                        ".": {},
                        "f:cpu": {},
                        "f:memory": {}
                      },
                      "f:requests": {
                        ".": {},
                        "f:cpu": {},
                        "f:memory": {}
                      }
                    },
                    "f:terminationMessagePath": {},
                    "f:terminationMessagePolicy": {},
                    "f:volumeMounts": {
                      ".": {},
                      "k:{\"mountPath\":\"/cassandra-base-config\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      },
                      "k:{\"mountPath\":\"/config\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      }
                    }
                  },
                  "k:{\"name\":\"server-config-init-base\"}": {
                    ".": {},
                    "f:args": {},
                    "f:command": {},
                    "f:image": {},
                    "f:imagePullPolicy": {},
                    "f:name": {},
                    "f:resources": {},
                    "f:terminationMessagePath": {},
                    "f:terminationMessagePolicy": {},
                    "f:volumeMounts": {
                      ".": {},
                      "k:{\"mountPath\":\"/cassandra-base-config\"}": {
                        ".": {},
                        "f:mountPath": {},
                        "f:name": {}
                      }
                    }
                  }
                },
                "f:restartPolicy": {},
                "f:schedulerName": {},
                "f:securityContext": {
                  ".": {},
                  "f:fsGroup": {},
                  "f:runAsGroup": {},
                  "f:runAsNonRoot": {},
                  "f:runAsUser": {}
                },
                "f:terminationGracePeriodSeconds": {},
                "f:volumes": {
                  ".": {},
                  "k:{\"name\":\"server-config\"}": {
                    ".": {},
                    "f:emptyDir": {},
                    "f:name": {}
                  },
                  "k:{\"name\":\"server-config-base\"}": {
                    ".": {},
                    "f:emptyDir": {},
                    "f:name": {}
                  },
                  "k:{\"name\":\"server-logs\"}": {
                    ".": {},
                    "f:emptyDir": {},
                    "f:name": {}
                  },
                  "k:{\"name\":\"vector-lib\"}": {
                    ".": {},
                    "f:emptyDir": {},
                    "f:name": {}
                  }
                }
              }
            },
            "f:updateStrategy": {
              "f:rollingUpdate": {
                ".": {},
                "f:partition": {}
              },
              "f:type": {}
            },
            "f:volumeClaimTemplates": {}
          }
        },
        "manager": "main",
        "operation": "Update",
        "time": "2025-03-28T04:10:31Z"
      },
      {
        "apiVersion": "apps/v1",
        "fieldsType": "FieldsV1",
        "fieldsV1": {
          "f:status": {
            "f:collisionCount": {},
            "f:currentRevision": {},
            "f:observedGeneration": {},
            "f:replicas": {},
            "f:updateRevision": {}
          }
        },
        "manager": "kube-controller-manager",
        "operation": "Update",
        "subresource": "status",
        "time": "2025-03-28T04:10:32Z"
      }
    ],
    "name": "sleevecdc-sample-dc-sample-rack-sts",
    "namespace": "tracey",
    "ownerReferences": [
      {
        "apiVersion": "cassandra.datastax.com/v1beta1",
        "blockOwnerDeletion": true,
        "controller": true,
        "kind": "CassandraDatacenter",
        "name": "sample-dc",
        "uid": "f41bd5db-5b03-483a-8eb6-ab7aba48b540"
      }
    ],
    "resourceVersion": "11176455",
    "uid": "fbf1e4ce-0f26-401b-86a5-e182a697a975"
  },
  "spec": {
    "minReadySeconds": 5,
    "podManagementPolicy": "Parallel",
    "replicas": 0,
    "revisionHistoryLimit": 10,
    "selector": {
      "matchLabels": {
        "cassandra.datastax.com/cluster": "sleevecdc",
        "cassandra.datastax.com/datacenter": "sample-dc",
        "cassandra.datastax.com/rack": "sample-rack"
      }
    },
    "serviceName": "sleevecdc-sample-dc-all-pods-service",
    "template": {
      "metadata": {
        "creationTimestamp": null,
        "labels": {
          "app.kubernetes.io/created-by": "cass-operator",
          "app.kubernetes.io/instance": "cassandra-sleevecdc",
          "app.kubernetes.io/managed-by": "cass-operator",
          "app.kubernetes.io/name": "cassandra",
          "app.kubernetes.io/version": "4.1.5",
          "cassandra.datastax.com/cluster": "sleevecdc",
          "cassandra.datastax.com/datacenter": "sample-dc",
          "cassandra.datastax.com/node-state": "Ready-to-Start",
          "cassandra.datastax.com/rack": "sample-rack"
        }
      },
      "spec": {
        "affinity": {},
        "containers": [
          {
            "env": [
              {
                "name": "POD_NAME",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "metadata.name"
                  }
                }
              },
              {
                "name": "NODE_NAME",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "spec.nodeName"
                  }
                }
              },
              {
                "name": "DS_LICENSE",
                "value": "accept"
              },
              {
                "name": "USE_MGMT_API",
                "value": "true"
              },
              {
                "name": "MGMT_API_NO_KEEP_ALIVE",
                "value": "true"
              },
              {
                "name": "MGMT_API_EXPLICIT_START",
                "value": "true"
              }
            ],
            "image": "k8ssandra/cass-management-api:4.1.5-ubi",
            "imagePullPolicy": "IfNotPresent",
            "lifecycle": {
              "preStop": {
                "exec": {
                  "command": [
                    "curl",
                    "-X",
                    "POST",
                    "-s",
                    "-m",
                    "0",
                    "-o",
                    "/dev/null",
                    "--show-error",
                    "--fail",
                    "http://localhost:8080/api/v0/ops/node/drain"
                  ]
                }
              }
            },
            "livenessProbe": {
              "failureThreshold": 3,
              "httpGet": {
                "path": "/api/v0/probes/liveness",
                "port": 8080,
                "scheme": "HTTP"
              },
              "initialDelaySeconds": 15,
              "periodSeconds": 15,
              "successThreshold": 1,
              "timeoutSeconds": 10
            },
            "name": "cassandra",
            "ports": [
              {
                "containerPort": 9042,
                "name": "native",
                "protocol": "TCP"
              },
              {
                "containerPort": 9142,
                "name": "tls-native",
                "protocol": "TCP"
              },
              {
                "containerPort": 7000,
                "name": "internode",
                "protocol": "TCP"
              },
              {
                "containerPort": 7001,
                "name": "tls-internode",
                "protocol": "TCP"
              },
              {
                "containerPort": 7199,
                "name": "jmx",
                "protocol": "TCP"
              },
              {
                "containerPort": 8080,
                "name": "mgmt-api-http",
                "protocol": "TCP"
              },
              {
                "containerPort": 9103,
                "name": "prometheus",
                "protocol": "TCP"
              },
              {
                "containerPort": 9000,
                "name": "metrics",
                "protocol": "TCP"
              }
            ],
            "readinessProbe": {
              "failureThreshold": 3,
              "httpGet": {
                "path": "/api/v0/probes/readiness",
                "port": 8080,
                "scheme": "HTTP"
              },
              "initialDelaySeconds": 20,
              "periodSeconds": 10,
              "successThreshold": 1,
              "timeoutSeconds": 10
            },
            "resources": {},
            "terminationMessagePath": "/dev/termination-log",
            "terminationMessagePolicy": "File",
            "volumeMounts": [
              {
                "mountPath": "/var/log/cassandra",
                "name": "server-logs"
              },
              {
                "mountPath": "/var/lib/cassandra",
                "name": "server-data"
              },
              {
                "mountPath": "/config",
                "name": "server-config"
              }
            ]
          },
          {
            "env": [
              {
                "name": "POD_NAME",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "metadata.name"
                  }
                }
              },
              {
                "name": "NODE_NAME",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "spec.nodeName"
                  }
                }
              },
              {
                "name": "CLUSTER_NAME",
                "value": "sleevecdc"
              },
              {
                "name": "DATACENTER_NAME",
                "value": "sample-dc"
              },
              {
                "name": "RACK_NAME",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "metadata.labels['cassandra.datastax.com/rack']"
                  }
                }
              },
              {
                "name": "NAMESPACE",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "metadata.namespace"
                  }
                }
              }
            ],
            "image": "k8ssandra/system-logger:v1.23.0",
            "imagePullPolicy": "IfNotPresent",
            "name": "server-system-logger",
            "resources": {
              "limits": {
                "memory": "128M"
              },
              "requests": {
                "cpu": "100m",
                "memory": "64M"
              }
            },
            "terminationMessagePath": "/dev/termination-log",
            "terminationMessagePolicy": "File",
            "volumeMounts": [
              {
                "mountPath": "/var/log/cassandra",
                "name": "server-logs"
              },
              {
                "mountPath": "/var/lib/vector",
                "name": "vector-lib"
              }
            ]
          }
        ],
        "dnsPolicy": "ClusterFirst",
        "initContainers": [
          {
            "args": [
              "-c",
              "cp -rf /etc/cassandra/* /cassandra-base-config/"
            ],
            "command": [
              "/bin/sh"
            ],
            "image": "k8ssandra/cass-management-api:4.1.5-ubi",
            "imagePullPolicy": "IfNotPresent",
            "name": "server-config-init-base",
            "resources": {},
            "terminationMessagePath": "/dev/termination-log",
            "terminationMessagePolicy": "File",
            "volumeMounts": [
              {
                "mountPath": "/cassandra-base-config",
                "name": "server-config-base"
              }
            ]
          },
          {
            "args": [
              "config",
              "build"
            ],
            "env": [
              {
                "name": "POD_IP",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "status.podIP"
                  }
                }
              },
              {
                "name": "HOST_IP",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion": "v1",
                    "fieldPath": "status.hostIP"
                  }
                }
              },
              {
                "name": "USE_HOST_IP_FOR_BROADCAST",
                "value": "false"
              },
              {
                "name": "RACK_NAME",
                "value": "sample-rack"
              },
              {
                "name": "PRODUCT_VERSION",
                "value": "4.1.5"
              },
              {
                "name": "PRODUCT_NAME",
                "value": "cassandra"
              },
              {
                "name": "CONFIG_FILE_DATA",
                "value": "{\"cassandra-yaml\":{},\"cluster-info\":{\"name\":\"sleevecdc\",\"seeds\":\"sleevecdc-seed-service,sleevecdc-sample-dc-additional-seed-service\"},\"datacenter-info\":{\"graph-enabled\":0,\"name\":\"sample-dc\",\"solr-enabled\":0,\"spark-enabled\":0},\"jvm-server-options\":{\"initial_heap_size\":\"800M\",\"max_heap_size\":\"800M\"}}"
              }
            ],
            "image": "k8ssandra/k8ssandra-client:v0.6.0",
            "imagePullPolicy": "IfNotPresent",
            "name": "server-config-init",
            "resources": {
              "limits": {
                "cpu": "1",
                "memory": "384M"
              },
              "requests": {
                "cpu": "1",
                "memory": "256M"
              }
            },
            "terminationMessagePath": "/dev/termination-log",
            "terminationMessagePolicy": "File",
            "volumeMounts": [
              {
                "mountPath": "/config",
                "name": "server-config"
              },
              {
                "mountPath": "/cassandra-base-config",
                "name": "server-config-base"
              }
            ]
          }
        ],
        "restartPolicy": "Always",
        "schedulerName": "default-scheduler",
        "securityContext": {
          "fsGroup": 999,
          "runAsGroup": 999,
          "runAsNonRoot": true,
          "runAsUser": 999
        },
        "terminationGracePeriodSeconds": 120,
        "volumes": [
          {
            "emptyDir": {},
            "name": "server-config"
          },
          {
            "emptyDir": {},
            "name": "server-logs"
          },
          {
            "emptyDir": {},
            "name": "server-config-base"
          },
          {
            "emptyDir": {},
            "name": "vector-lib"
          }
        ]
      }
    },
    "updateStrategy": {
      "rollingUpdate": {
        "partition": 0
      },
      "type": "RollingUpdate"
    },
    "volumeClaimTemplates": [
      {
        "metadata": {
          "annotations": {
            "cassandra.datastax.com/resource-hash": "7aVuAh04+l/t8FDW/ZMZaMGcNb96V6HQViwhmQMCSs4="
          },
          "creationTimestamp": null,
          "labels": {
            "app.kubernetes.io/created-by": "cass-operator",
            "app.kubernetes.io/instance": "cassandra-sleevecdc",
            "app.kubernetes.io/managed-by": "cass-operator",
            "app.kubernetes.io/name": "cassandra",
            "app.kubernetes.io/version": "4.1.5",
            "cassandra.datastax.com/cluster": "sleevecdc",
            "cassandra.datastax.com/datacenter": "sample-dc",
            "cassandra.datastax.com/rack": "sample-rack"
          },
          "name": "server-data"
        },
        "spec": {
          "accessModes": [
            "ReadWriteOnce"
          ],
          "resources": {
            "requests": {
              "storage": "1Gi"
            }
          },
          "storageClassName": "standard",
          "volumeMode": "Filesystem"
        },
        "status": {
          "phase": "Pending"
        }
      }
    ]
  },
  "status": {
    "availableReplicas": 0,
    "collisionCount": 0,
    "currentRevision": "sleevecdc-sample-dc-sample-rack-sts-56759657cd",
    "observedGeneration": 1,
    "replicas": 0,
    "updateRevision": "sleevecdc-sample-dc-sample-rack-sts-56759657cd"
  }
}
```

## Unique Paths: 1

Path 1:
```
	CassandraDatacenter:60ac9f15 (explore) - #changes=1
	PATCH: {StatefulSet/tracey/sleevecdc-sample-dc-sample-rack-sts:5f73135d-1f56-45dc-a8b5-838bd26a2e46}
	{StatefulSet/tracey/sleevecdc-sample-dc-sample-rack-sts:5f73135d-1f56-45dc-a8b5-838bd26a2e46}: {*unstructured.Unstructured}.Object["spec"].(map[string]any)["replicas"].(float64):
	-: 3
	+: 0

	StatefulSetController:f910bdda (explore) - #changes=3
	DELETE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["deletionTimestamp"]:
	-: <nil>
	+: 2025-01-01T00:00:00Z

{*unstructured.Unstructured}.Object["metadata"].(map[string]any)["labels"].(map[string]any)["discrete.events/deletion-id"]:
	-: <nil>
	+: 96487921-8ba7-4216-9c48-7263bfe75fc0

	DELETE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["deletionTimestamp"]:
	-: <nil>
	+: 2025-01-01T00:00:00Z

{*unstructured.Unstructured}.Object["metadata"].(map[string]any)["labels"].(map[string]any)["discrete.events/deletion-id"]:
	-: <nil>
	+: ab9df3f4-0635-4392-becb-e0e645dcfcdb

	DELETE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["deletionTimestamp"]:
	-: <nil>
	+: 2025-01-01T00:00:00Z

{*unstructured.Unstructured}.Object["metadata"].(map[string]any)["labels"].(map[string]any)["discrete.events/deletion-id"]:
	-: <nil>
	+: 24443d2e-db4d-481a-a46f-20638ecfe01c

	CleanupReconciler:4654dcf4 (explore) - #changes=1
	REMOVE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}: 
	StatefulSetController:9cc36d9f (explore) - #changes=2
	DELETE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}: 
	DELETE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}: 
	CleanupReconciler:ed2a13b5 (explore) - #changes=1
	REMOVE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}: 
	StatefulSetController:3230a308 (explore) - #changes=1
	DELETE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}: 
	CleanupReconciler:d434c2c4 (explore) - #changes=1
	REMOVE: {Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}
	{Pod/tracey/sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}: 
	StatefulSetController:813f5968 (explore) - #changes=1
	UPDATE: {StatefulSet/tracey/sleevecdc-sample-dc-sample-rack-sts:5f73135d-1f56-45dc-a8b5-838bd26a2e46}
	{StatefulSet/tracey/sleevecdc-sample-dc-sample-rack-sts:5f73135d-1f56-45dc-a8b5-838bd26a2e46}: {*unstructured.Unstructured}.Object["status"].(map[string]any)["replicas"].(float64):
	-: 3
	+: 0

	CassandraDatacenter:2b9f5ed2 (explore) - #changes=4
	DELETE: {PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}
	{PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["deletionTimestamp"]:
	-: <nil>
	+: 2025-01-01T00:00:00Z

{*unstructured.Unstructured}.Object["metadata"].(map[string]any)["labels"].(map[string]any)["discrete.events/deletion-id"]:
	-: <nil>
	+: d3f3a258-d7f1-47ae-af94-ed6ee618de15

	DELETE: {PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}
	{PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["deletionTimestamp"]:
	-: <nil>
	+: 2025-01-01T00:00:00Z

{*unstructured.Unstructured}.Object["metadata"].(map[string]any)["labels"].(map[string]any)["discrete.events/deletion-id"]:
	-: <nil>
	+: 4f62c384-a417-4e05-9c85-0ded3bd6973d

	DELETE: {PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}
	{PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["deletionTimestamp"]:
	-: <nil>
	+: 2025-01-01T00:00:00Z

{*unstructured.Unstructured}.Object["metadata"].(map[string]any)["labels"].(map[string]any)["discrete.events/deletion-id"]:
	-: <nil>
	+: abbec9be-cfeb-44cd-9029-fe839d553464

	UPDATE: {CassandraDatacenter/tracey/sample-dc:264b14f9-6b37-470f-8777-518ac6b3c6b9}
	{CassandraDatacenter/tracey/sample-dc:264b14f9-6b37-470f-8777-518ac6b3c6b9}: {*unstructured.Unstructured}.Object["metadata"].(map[string]any)["finalizers"]:
	-: [finalizer.cassandra.datastax.com]
	+: <nil>

{*unstructured.Unstructured}.Object["status"].(map[string]any)["lastRollingRestart"]:
	-: <nil>
	+: 1970-01-01T00:00:01Z

{*unstructured.Unstructured}.Object["status"].(map[string]any)["lastServerNodeStarted"]:
	-: <nil>
	+: 1970-01-01T00:00:01Z

{*unstructured.Unstructured}.Object["status"].(map[string]any)["superUserUpserted"]:
	-: <nil>
	+: 1970-01-01T00:00:01Z

	CleanupReconciler:6bd77181 (explore) - #changes=1
	REMOVE: {PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}
	{PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-0:6d779056-8101-4e72-b04b-031bd05e09c1}: 
	CleanupReconciler:e59529a8 (explore) - #changes=1
	REMOVE: {PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}
	{PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-1:2d631b0f-7b2f-43a2-b547-9ebc070a5fc9}: 
	CleanupReconciler:7feadee5 (explore) - #changes=1
	REMOVE: {PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}
	{PersistentVolumeClaim/tracey/server-data-sleevecdc-sample-dc-sample-rack-sts-2:6091f9d5-15d1-47f4-802d-191718351a8d}: 
```
