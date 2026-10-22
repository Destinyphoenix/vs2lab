{
  description = "VS2Lab (Verteilte Systeme 2, HKA) – Python + Redis dev shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            # Redis ist je nach Version nicht als "free" eingestuft -> nur dafür freigeben
            config.allowUnfreePredicate = pkg: (nixpkgs.lib.getName pkg) == "redis";
          };

          # Entspricht dem Pipfile des Labors
          pythonEnv = pkgs.python3.withPackages (ps: with ps; [
            redis
            rpyc
            pyzmq # PyPI-Name: zmq
            ipython
            ipykernel
            jupyter
            jupyter-server
            ipyparallel
            # dev-packages
            pylint
            autopep8
            rope
          ]);

          # Redis lokal im Projekt starten/stoppen, ohne System-Dienst
          redisStart = pkgs.writeShellScriptBin "redis-start" ''
            dir="''${PWD}/.redis"
            mkdir -p "$dir"
            if [ -f "$dir/redis.pid" ] && kill -0 "$(cat "$dir/redis.pid")" 2>/dev/null; then
              echo "Redis läuft bereits (PID $(cat "$dir/redis.pid"))"
              exit 0
            fi
            ${pkgs.redis}/bin/redis-server \
              --daemonize yes \
              --bind 127.0.0.1 \
              --port 6379 \
              --dir "$dir" \
              --pidfile "$dir/redis.pid" \
              --logfile "$dir/redis.log"
            echo "Redis gestartet auf 127.0.0.1:6379"
          '';

          redisStop = pkgs.writeShellScriptBin "redis-stop" ''
            ${pkgs.redis}/bin/redis-cli -p 6379 shutdown nosave 2>/dev/null \
              && echo "Redis gestoppt" || echo "Redis lief nicht"
          '';
        in
        {
          default = pkgs.mkShell {
            name = "vs2lab";
            packages = [
              pythonEnv
              pkgs.redis
              redisStart
              redisStop
              pkgs.git
            ];

            shellHook = ''
              echo "VS2Lab shell – $(python --version)"
              echo "  redis-start / redis-stop   lokaler Redis (ab Labor 2)"
              echo "  jupyter notebook --ip 127.0.0.1"
            '';
          };
        });
    };
}
