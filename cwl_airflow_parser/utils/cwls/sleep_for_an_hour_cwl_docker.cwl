class: Workflow
cwlVersion: v1.0


inputs:
  delay:
    type: int
    default: 600


outputs:

  empty_file:
    type: File?
    outputSource: sleep_6/empty_file

steps:

  sleep_1:
    in:
      delay: delay
    out: [empty_file]
    run:
      class: CommandLineTool
      cwlVersion: v1.0
      hints:
        - class: DockerRequirement
          dockerPull: ubuntu:xenial
      baseCommand: [sleep]
      inputs:
        delay:
          type: int
          inputBinding:
            position: 1
        dummy_input:
          type: File?
      outputs:
        empty_file:
          type: File?
          outputBinding:
            glob: "*"

  sleep_2:
    in:
      delay: delay
      dummy_input: sleep_1/empty_file
    out: [empty_file]
    run:
      class: CommandLineTool
      cwlVersion: v1.0
      hints:
        - class: DockerRequirement
          dockerPull: ubuntu:xenial
      baseCommand: [sleep]
      inputs:
        delay:
          type: int
          inputBinding:
            position: 1
        dummy_input:
          type: File?
      outputs:
        empty_file:
          type: File?
          outputBinding:
            glob: "*"

  sleep_3:
    in:
      delay: delay
      dummy_input: sleep_2/empty_file
    out: [empty_file]
    run:
      class: CommandLineTool
      cwlVersion: v1.0
      hints:
        - class: DockerRequirement
          dockerPull: ubuntu:xenial
      baseCommand: [sleep]
      inputs:
        delay:
          type: int
          inputBinding:
            position: 1
        dummy_input:
          type: File?
      outputs:
        empty_file:
          type: File?
          outputBinding:
            glob: "*"

  sleep_4:
    in:
      delay: delay
      dummy_input: sleep_3/empty_file
    out: [empty_file]
    run:
      class: CommandLineTool
      cwlVersion: v1.0
      hints:
        - class: DockerRequirement
          dockerPull: ubuntu:xenial
      baseCommand: [sleep]
      inputs:
        delay:
          type: int
          inputBinding:
            position: 1
        dummy_input:
          type: File?
      outputs:
        empty_file:
          type: File?
          outputBinding:
            glob: "*"

  sleep_5:
    in:
      delay: delay
      dummy_input: sleep_4/empty_file
    out: [empty_file]
    run:
      class: CommandLineTool
      cwlVersion: v1.0
      hints:
        - class: DockerRequirement
          dockerPull: ubuntu:xenial
      baseCommand: [sleep]
      inputs:
        delay:
          type: int
          inputBinding:
            position: 1
        dummy_input:
          type: File?
      outputs:
        empty_file:
          type: File?
          outputBinding:
            glob: "*"

  sleep_6:
    in:
      delay: delay
      dummy_input: sleep_5/empty_file
    out: [empty_file]
    run:
      class: CommandLineTool
      cwlVersion: v1.0
      hints:
        - class: DockerRequirement
          dockerPull: ubuntu:xenial
      baseCommand: [sleep]
      inputs:
        delay:
          type: int
          inputBinding:
            position: 1
        dummy_input:
          type: File?
      outputs:
        empty_file:
          type: File?
          outputBinding:
            glob: "*"