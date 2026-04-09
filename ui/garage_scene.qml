import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils

Rectangle {
    id: root
    color: "#000000"

    property real currentYaw: 24
    property real targetYaw: 24
    property real currentPitch: 9
    property real targetPitch: 9
    property real currentDistance: 12.8
    property real targetDistance: 12.8
    property real idleSpeed: 0.82
    property bool dragging: false
    property real lastMouseX: 0
    property real lastMouseY: 0
    property int loaderStatus: carLoader.status
    property string loaderError: carLoader.errorString
    property real modelScale: 1.0
    property real platformY: -1.88

    function updateCamera() {
        var yaw = currentYaw * Math.PI / 180.0
        var pitch = currentPitch * Math.PI / 180.0
        var horizontal = currentDistance * Math.cos(pitch)
        orbitCamera.position.x = Math.sin(yaw) * horizontal
        orbitCamera.position.y = 1.55 + Math.sin(pitch) * currentDistance
        orbitCamera.position.z = 2.0 + Math.cos(yaw) * horizontal
        orbitCamera.eulerRotation.x = -currentPitch
        orbitCamera.eulerRotation.y = currentYaw + 180.0
        orbitCamera.eulerRotation.z = 0
    }

    Image {
        anchors.fill: parent
        source: garageSceneBridge ? garageSceneBridge.backgroundUrl : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        smooth: true
        cache: true
    }

    Timer {
        interval: 16
        repeat: true
        running: true
        onTriggered: {
            if (!root.dragging)
                root.targetYaw += root.idleSpeed
            root.currentYaw += (root.targetYaw - root.currentYaw) * 0.25
            root.currentPitch += (root.targetPitch - root.currentPitch) * 0.20
            root.currentDistance += (root.targetDistance - root.currentDistance) * 0.22
            root.updateCamera()
            if (garageSceneBridge) {
                garageSceneBridge.cameraYaw = root.currentYaw
                garageSceneBridge.cameraPitch = root.currentPitch
            }
        }
    }

    View3D {
        anchors.fill: parent
        camera: orbitCamera
        visible: carLoader.status === RuntimeLoader.Success || carLoader.status === RuntimeLoader.Loading

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            temporalAAEnabled: true
            depthPrePassEnabled: true
        }

        PerspectiveCamera {
            id: orbitCamera
            clipNear: 0.1
            clipFar: 5000
            fieldOfView: 32
        }

        DirectionalLight {
            eulerRotation.x: -28
            eulerRotation.y: -18
            brightness: 1.55
            castsShadow: false
            ambientColor: "#597a8c"
            color: "#f1fbff"
        }

        PointLight {
            position: Qt.vector3d(-4.8, 4.0, 2.5)
            brightness: 58
            color: "#00e5ff"
            quadraticFade: 0.03
        }

        PointLight {
            position: Qt.vector3d(4.5, 2.8, -1.8)
            brightness: 14
            color: "#b100ff"
            quadraticFade: 0.045
        }

        Node {
            id: modelRig
            y: root.platformY
            z: -0.12
            scale: Qt.vector3d(root.modelScale, root.modelScale, root.modelScale)

            RuntimeLoader {
                id: carLoader
                source: garageSceneBridge ? garageSceneBridge.modelUrl : ""

                onStatusChanged: {
                    if (status !== RuntimeLoader.Success)
                        return
                    const min = bounds.minimum
                    const max = bounds.maximum
                    const sizeX = max.x - min.x
                    const sizeY = max.y - min.y
                    const sizeZ = max.z - min.z
                    const maxDim = Math.max(sizeX, sizeY, sizeZ, 0.001)
                    const centerX = (min.x + max.x) * 0.5
                    const centerZ = (min.z + max.z) * 0.5
                    root.modelScale = 5.6 / maxDim
                    carLoader.position = Qt.vector3d(-centerX, -min.y, -centerZ)
                }
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true

        onPressed: function(mouse) {
            root.dragging = true
            root.lastMouseX = mouse.x
            root.lastMouseY = mouse.y
        }

        onReleased: root.dragging = false
        onCanceled: root.dragging = false

        onPositionChanged: function(mouse) {
            if (!root.dragging)
                return
            var dx = mouse.x - root.lastMouseX
            var dy = mouse.y - root.lastMouseY
            root.targetYaw -= dx * 0.62
            root.targetPitch = Math.max(4, Math.min(16, root.targetPitch - dy * 0.16))
            root.lastMouseX = mouse.x
            root.lastMouseY = mouse.y
        }
    }
}
