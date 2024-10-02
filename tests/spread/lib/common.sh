export PATH=/snap/bin:$PROJECT_PATH/tests/spread/lib/tools:$PATH
export CONTROLLER_NAME="craft-test-$PROVIDER"

install_microk8s() {
    snap install microk8s --channel "$MICROK8S_CHANNEL"
    snap refresh microk8s --channel "$MICROK8S_CHANNEL"
    microk8s status --wait-ready

    if [ ! -z "$MICROK8S_ADDONS" ]; then
        microk8s enable $MICROK8S_ADDONS
    fi

    microk8s enable metallb:"$METALLB_RANGE"

    microk8s kubectl wait --for=condition=available --timeout=5m -nkube-system deployment/coredns deployment/hostpath-provisioner
    microk8s kubectl auth can-i create pods
}

install_juju() {
    snap install juju --classic --channel "$JUJU_CHANNEL"
    mkdir -p "$HOME"/.local/share/juju
}

bootstrap_juju() {
    agent_version="$(snap info juju | grep "$JUJU_CHANNEL" | tr "\n" " " | tr -s " " | cut -d " " -f4)"

    juju bootstrap --verbose "$PROVIDER" "$CONTROLLER_NAME" \
      $JUJU_BOOTSTRAP_OPTIONS $JUJU_EXTRA_BOOTSTRAP_OPTIONS \
      --bootstrap-constraints=$JUJU_BOOTSTRAP_CONSTRAINTS \
      --agent-version="$agent_version"
}

install_tools() {
    apt-get install -y make
    snap install astral-uv --classic
    snap install charmcraft --classic --channel "$CHARMCRAFT_CHANNEL"
    snap install jq
    snap install kubectl --classic
    snap install yq
    mkdir -p "$HOME"/.kube
    microk8s config > ${HOME}/.kube/config
}

setup_test_environment() {
  install_juju
  install_microk8s
  install_tools
  bootstrap_juju
  juju add-model testing
}

restore_test_environment() {
  rm -rf "$HOME"/.kube
  rm -rf "$HOME"/.local/share/juju

  snap remove --purge astral-uv
  snap remove --purge charmcraft
  snap remove --purge jq
  snap remove --purge juju
  snap remove --purge kubectl
  snap remove --purge microk8s
  snap remove --purge yq
}
